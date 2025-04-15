import os
import json
import datetime
import time
import hashlib
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, LargeBinary, MetaData, Table, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import base64
import io

# Get database URL from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")

# Create SQLAlchemy engine with connection pooling
if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,  # Number of connections to keep open
        max_overflow=10,  # Max number of connections to create when pool is full
        pool_timeout=30,  # Timeout for getting connection from pool
        pool_recycle=1800,  # Recycle connections after 30 minutes
        pool_pre_ping=True  # Test connections with a ping before using
    )
else:
    # Provide a fallback for development/testing
    st.warning("Database URL not found. Using in-memory SQLite database for testing.")
    engine = create_engine('sqlite:///:memory:')

# Create base class for declarative models
Base = declarative_base()

# Define metadata object
metadata = MetaData()

# Function to get raw database connection
def get_db_connection():
    """Get a raw database connection for direct SQL operations."""
    import psycopg2
    try:
        # Parse the DATABASE_URL to get connection parameters
        # Expected format: postgresql://username:password@host:port/database
        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            st.error("Database URL not found. Please check your environment configuration.")
            return None
            
        # Connect to the database
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

# Define tables using SQLAlchemy's Table construct
users = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('email', String(255), nullable=False, unique=True),
    Column('password_hash', String(255), nullable=False),
    Column('full_name', String(255), nullable=True),
    Column('created_at', DateTime, default=datetime.datetime.utcnow),
    Column('last_login', DateTime, nullable=True),
    Column('subscription_tier', String(50), default='free'),
    Column('subscription_start_date', DateTime, nullable=True),
    Column('subscription_end_date', DateTime, nullable=True),
    Column('is_trial', Integer, default=0),  # Boolean (0 or 1)
    Column('trial_start_date', DateTime, nullable=True),
    Column('trial_end_date', DateTime, nullable=True),
    Column('is_admin', Integer, default=0)  # Boolean (0 or 1)
)

password_reset_tokens = Table(
    'password_reset_tokens',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, nullable=False),
    Column('token', String(255), nullable=False, unique=True),
    Column('created_at', DateTime, default=datetime.datetime.utcnow),
    Column('expires_at', DateTime, nullable=False),
    Column('used', Integer, default=0)  # Boolean (0 or 1)
)

datasets = Table(
    'datasets', 
    metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, nullable=True),  # Foreign key to users table
    Column('name', String(255), nullable=False),
    Column('description', Text, nullable=True),
    Column('file_name', String(255), nullable=False),
    Column('file_type', String(50), nullable=False),
    Column('created_at', DateTime, default=datetime.datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow),
    Column('data', LargeBinary, nullable=False),  # Serialized DataFrame
    Column('column_types', Text, nullable=False),  # JSON string of column types
    Column('row_count', Integer, nullable=False),
    Column('column_count', Integer, nullable=False)
)

transformations = Table(
    'transformations',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('dataset_id', Integer, nullable=False),
    Column('name', String(255), nullable=False),
    Column('description', Text, nullable=True),
    Column('created_at', DateTime, default=datetime.datetime.utcnow),
    Column('transformation_json', Text, nullable=False),  # JSON string of transformation details
    Column('affected_columns', Text, nullable=False)  # JSON string of affected columns
)

versions = Table(
    'versions',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('dataset_id', Integer, nullable=False),
    Column('version_number', Integer, nullable=False),
    Column('name', String(255), nullable=False),
    Column('description', Text, nullable=True),
    Column('created_at', DateTime, default=datetime.datetime.utcnow),
    Column('data', LargeBinary, nullable=False),  # Serialized DataFrame
    Column('transformations_applied', Text, nullable=False),  # JSON string of applied transformations
    Column('row_count', Integer, nullable=False),
    Column('column_count', Integer, nullable=False)
)

insights = Table(
    'insights',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('dataset_id', Integer, nullable=False),
    Column('version_id', Integer, nullable=True),
    Column('name', String(255), nullable=False),
    Column('type', String(50), nullable=False),  # e.g., 'correlation', 'outlier', 'distribution'
    Column('created_at', DateTime, default=datetime.datetime.utcnow),
    Column('insight_json', Text, nullable=False),  # JSON string of insight details
    Column('importance', Integer, nullable=True)  # 1-5 rating of importance
)

# Create tables if they don't exist
def initialize_database():
    """Create database tables if they don't exist."""
    inspector = inspect(engine)
    
    # Check if essential tables exist and create them if they don't
    if not inspector.has_table('datasets') or not inspector.has_table('users'):
        metadata.create_all(engine)
        st.success("Database initialized successfully.")
        return True
    
    # Check for password_reset_tokens table specifically
    if not inspector.has_table('password_reset_tokens'):
        metadata.tables['password_reset_tokens'].create(engine)
        st.info("Password reset functionality initialized.")
        return True
        
    return False

# Session factory with connection pooling and thread safety
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# Helper function for database operations with retry logic
def execute_with_retry(operation, max_retries=3, retry_delay=1):
    """Execute a database operation with retry logic."""
    retries = 0
    while retries < max_retries:
        try:
            return operation()
        except (OperationalError, SQLAlchemyError) as e:
            retries += 1
            if "SSL connection has been closed unexpectedly" in str(e) and retries < max_retries:
                # SSL connection error, wait and retry
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                st.warning(f"Database connection lost. Retrying... ({retries}/{max_retries})")
            else:
                if retries == max_retries:
                    st.error(f"Database error after {max_retries} retries: {str(e)}")
                raise

# DataFrame serialization/deserialization
def serialize_dataframe(df):
    """Serialize a pandas DataFrame to bytes."""
    output = io.BytesIO()
    df.to_parquet(output)
    return output.getvalue()

def deserialize_dataframe(data):
    """Deserialize bytes back to a pandas DataFrame."""
    try:
        return pd.read_parquet(io.BytesIO(data))
    except Exception as e:
        st.error(f"Error deserializing DataFrame: {str(e)}")
        return None

# Dataset operations
def save_dataset(name, description, file_name, file_type, df, column_types, user_id=None):
    """Save a dataset to the database."""
    session = Session()
    try:
        serialized_data = serialize_dataframe(df)
        column_types_json = json.dumps(column_types)
        
        # Get user_id from session state if not provided
        if user_id is None and "user_id" in st.session_state:
            user_id = st.session_state.user_id
        
        # Convert numpy.int64 to regular Python int if needed
        if user_id is not None and hasattr(user_id, 'item'):
            user_id = int(user_id)
        
        # Check if dataset with same name exists
        existing = session.query(datasets).filter(datasets.c.name == name)
        
        # Filter by user_id if available
        if user_id:
            existing = existing.filter(datasets.c.user_id == user_id)
            
        existing = existing.first()
        
        if existing:
            # Update existing dataset
            session.execute(
                datasets.update().where(datasets.c.id == existing.id).values(
                    description=description,
                    file_name=file_name,
                    file_type=file_type,
                    updated_at=datetime.datetime.utcnow(),
                    data=serialized_data,
                    column_types=column_types_json,
                    row_count=df.shape[0],
                    column_count=df.shape[1],
                    user_id=user_id
                )
            )
            dataset_id = existing.id
        else:
            # Insert new dataset
            result = session.execute(
                datasets.insert().values(
                    name=name,
                    description=description,
                    file_name=file_name,
                    file_type=file_type,
                    data=serialized_data,
                    column_types=column_types_json,
                    row_count=df.shape[0],
                    column_count=df.shape[1],
                    user_id=user_id
                )
            )
            dataset_id = result.inserted_primary_key[0]
        
        session.commit()
        return dataset_id
    except Exception as e:
        session.rollback()
        st.error(f"Error saving dataset: {str(e)}")
        return None
    finally:
        session.close()

def get_dataset(dataset_id, user_id=None):
    """Retrieve a dataset from the database with retry logic."""
    def _get_dataset_operation():
        session = Session()
        try:
            # Get user_id from session state if not provided
            if user_id is None and "user_id" in st.session_state:
                current_user_id = st.session_state.user_id
            else:
                current_user_id = user_id
            
            # Convert dataset_id to int, handling various types safely
            try:
                if hasattr(dataset_id, 'item'):
                    dataset_id_int = dataset_id.item()
                else:
                    dataset_id_int = int(dataset_id)
            except (ValueError, TypeError) as e:
                st.error(f"Invalid dataset ID format: {str(e)}")
                return None
                
            # Build the query
            query = session.query(datasets).filter(datasets.c.id == dataset_id_int)
            
            # Apply user_id filter if provided
            if current_user_id:
                try:
                    # Convert user_id to int if needed
                    if hasattr(current_user_id, 'item'):
                        current_user_id_int = current_user_id.item()
                    else:
                        current_user_id_int = int(current_user_id)
                    query = query.filter(datasets.c.user_id == current_user_id_int)
                except (ValueError, TypeError) as e:
                    st.error(f"Invalid user ID format: {str(e)}")
                    return None
            
            result = query.first()
            
            if result:
                try:
                    df = deserialize_dataframe(result.data)
                    column_types = json.loads(result.column_types)
                    
                    return {
                        'id': result.id,
                        'name': result.name,
                        'description': result.description,
                        'file_name': result.file_name,
                        'file_type': result.file_type,
                        'created_at': result.created_at,
                        'updated_at': result.updated_at,
                        'dataset': df,
                        'column_types': column_types,
                        'row_count': result.row_count,
                        'column_count': result.column_count,
                        'user_id': result.user_id
                    }
                except Exception as e:
                    st.error(f"Error deserializing dataset: {str(e)}")
                    return None
            else:
                st.warning(f"Dataset with ID {dataset_id} not found in database.")
                return None
        except Exception as e:
            if not isinstance(e, (OperationalError, SQLAlchemyError)):
                st.error(f"Error retrieving dataset: {str(e)}")
            raise
        finally:
            session.close()
    
    try:
        return execute_with_retry(_get_dataset_operation)
    except Exception as e:
        st.error(f"Failed to retrieve dataset after retries: {str(e)}")
        return None

def list_datasets(user_id=None):
    """List datasets in the database with retry logic, filtered by user_id if provided."""
    def _list_datasets_operation():
        session = Session()
        try:
            query = session.query(datasets)
            
            # Use non-local variable to store user_id
            current_user_id = user_id
            
            # Filter by user_id if provided or available in session state
            if current_user_id is None and "user_id" in st.session_state:
                current_user_id = st.session_state.user_id
                
            if current_user_id:
                # Convert user_id to int if needed (for numpy.int64)
                if hasattr(current_user_id, 'item'):
                    current_user_id_int = current_user_id.item()
                else:
                    current_user_id_int = int(current_user_id)
                query = query.filter(datasets.c.user_id == current_user_id_int)
                
            results = query.all()
            
            dataset_list = [
                {
                    'id': row.id,
                    'name': row.name,
                    'description': row.description,
                    'file_name': row.file_name,
                    'file_type': row.file_type,
                    'created_at': row.created_at,
                    'updated_at': row.updated_at,
                    'row_count': row.row_count,
                    'column_count': row.column_count,
                    'user_id': row.user_id
                }
                for row in results
            ]
            
            return dataset_list
        except Exception as e:
            if not isinstance(e, (OperationalError, SQLAlchemyError)):
                st.error(f"Error listing datasets: {str(e)}")
            raise
        finally:
            session.close()
    
    try:
        return execute_with_retry(_list_datasets_operation)
    except Exception as e:
        st.error(f"Failed to list datasets after retries: {str(e)}")
        return []

def delete_dataset(dataset_id, user_id=None):
    """Delete a dataset and all related records, with optional user_id check."""
    session = Session()
    try:
        # Get user_id from session state if not provided
        current_user_id = user_id
        if current_user_id is None and "user_id" in st.session_state:
            current_user_id = st.session_state.user_id
        
        # Convert numpy.int64 to int if needed
        if hasattr(dataset_id, 'item'):
            dataset_id_int = dataset_id.item()
        else:
            dataset_id_int = int(dataset_id)
            
        # Convert user_id to int if needed
        if current_user_id and hasattr(current_user_id, 'item'):
            current_user_id_int = current_user_id.item()
        elif current_user_id:
            current_user_id_int = int(current_user_id)
        else:
            current_user_id_int = None
            
        # Check if dataset exists and belongs to the user
        dataset = None
        if current_user_id_int:
            dataset = session.query(datasets).filter(datasets.c.id == dataset_id_int, datasets.c.user_id == current_user_id_int).first()
        else:
            dataset = session.query(datasets).filter(datasets.c.id == dataset_id_int).first()
            
        if not dataset:
            st.error(f"Dataset not found or you don't have permission to delete it.")
            return False
            
        # Delete related records first
        session.execute(transformations.delete().where(transformations.c.dataset_id == dataset_id_int))
        session.execute(versions.delete().where(versions.c.dataset_id == dataset_id_int))
        session.execute(insights.delete().where(insights.c.dataset_id == dataset_id_int))
        
        # Delete the dataset
        session.execute(datasets.delete().where(datasets.c.id == dataset_id_int))
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"Error deleting dataset: {str(e)}")
        return False
    finally:
        session.close()

# Transformation operations
def save_transformation(dataset_id, name, description, transformation_details, affected_columns):
    """Save a transformation to the database."""
    session = Session()
    try:
        transformation_json = json.dumps(transformation_details)
        affected_columns_json = json.dumps(affected_columns)
        
        # Convert numpy.int64 to regular Python int if needed
        if hasattr(dataset_id, 'item'):
            dataset_id = int(dataset_id)
        
        result = session.execute(
            transformations.insert().values(
                dataset_id=dataset_id,
                name=name,
                description=description,
                transformation_json=transformation_json,
                affected_columns=affected_columns_json
            )
        )
        
        session.commit()
        return result.inserted_primary_key[0]
    except Exception as e:
        session.rollback()
        st.error(f"Error saving transformation: {str(e)}")
        return None
    finally:
        session.close()

def get_transformations(dataset_id):
    """Get all transformations for a dataset with retry logic."""
    def _get_transformations_operation():
        session = Session()
        try:
            # Convert numpy.int64 to regular Python int if needed
            if hasattr(dataset_id, 'item'):
                dataset_id_int = int(dataset_id)
            else:
                dataset_id_int = dataset_id
                
            results = session.query(transformations).filter(transformations.c.dataset_id == dataset_id_int).all()
            
            transformation_list = [
                {
                    'id': row.id,
                    'name': row.name,
                    'description': row.description,
                    'created_at': row.created_at,
                    'details': json.loads(row.transformation_json),
                    'affected_columns': json.loads(row.affected_columns)
                }
                for row in results
            ]
            
            return transformation_list
        except Exception as e:
            if not isinstance(e, (OperationalError, SQLAlchemyError)):
                st.error(f"Error retrieving transformations: {str(e)}")
            raise
        finally:
            session.close()
    
    try:
        return execute_with_retry(_get_transformations_operation)
    except Exception as e:
        st.error(f"Failed to retrieve transformations after retries: {str(e)}")
        return []

# Version operations
def save_version(dataset_id, version_number, name, description, df, transformations_applied):
    """Save a version of a dataset."""
    session = Session()
    try:
        serialized_data = serialize_dataframe(df)
        transformations_json = json.dumps(transformations_applied)
        
        # Convert numpy.int64 to regular Python int
        if hasattr(dataset_id, 'item'):
            dataset_id = int(dataset_id)
        
        result = session.execute(
            versions.insert().values(
                dataset_id=dataset_id,
                version_number=version_number,
                name=name,
                description=description,
                data=serialized_data,
                transformations_applied=transformations_json,
                row_count=int(df.shape[0]),
                column_count=int(df.shape[1])
            )
        )
        
        session.commit()
        return result.inserted_primary_key[0]
    except Exception as e:
        session.rollback()
        st.error(f"Error saving version: {str(e)}")
        return None
    finally:
        session.close()

def get_version(version_id):
    """Get a specific version with retry logic."""
    def _get_version_operation():
        session = Session()
        try:
            # Convert numpy.int64 to regular Python int if needed
            if hasattr(version_id, 'item'):
                version_id_int = int(version_id)
            else:
                version_id_int = version_id
                
            result = session.query(versions).filter(versions.c.id == version_id_int).first()
            
            if result:
                df = deserialize_dataframe(result.data)
                transformations_applied = json.loads(result.transformations_applied)
                
                return {
                    'id': result.id,
                    'dataset_id': result.dataset_id,
                    'version_number': result.version_number,
                    'name': result.name,
                    'description': result.description,
                    'created_at': result.created_at,
                    'dataset': df,
                    'transformations_applied': transformations_applied,
                    'row_count': result.row_count,
                    'column_count': result.column_count
                }
            return None
        except Exception as e:
            if not isinstance(e, (OperationalError, SQLAlchemyError)):
                st.error(f"Error retrieving version: {str(e)}")
            raise
        finally:
            session.close()
            
    try:
        return execute_with_retry(_get_version_operation)
    except Exception as e:
        st.error(f"Failed to retrieve version after retries: {str(e)}")
        return None

def get_versions(dataset_id):
    """Get all versions for a dataset with retry logic."""
    def _get_versions_operation():
        session = Session()
        try:
            # Convert numpy.int64 to regular Python int if needed
            if hasattr(dataset_id, 'item'):
                dataset_id_int = int(dataset_id)
            else:
                dataset_id_int = dataset_id
                
            results = session.query(versions).filter(versions.c.dataset_id == dataset_id_int).all()
            
            version_list = [
                {
                    'id': row.id,
                    'version_number': row.version_number,
                    'name': row.name,
                    'description': row.description,
                    'created_at': row.created_at,
                    'row_count': row.row_count,
                    'column_count': row.column_count,
                    'transformations_count': len(json.loads(row.transformations_applied))
                }
                for row in results
            ]
            
            return version_list
        except Exception as e:
            if not isinstance(e, (OperationalError, SQLAlchemyError)):
                st.error(f"Error retrieving versions: {str(e)}")
            raise
        finally:
            session.close()
    
    try:
        return execute_with_retry(_get_versions_operation)
    except Exception as e:
        st.error(f"Failed to retrieve versions after retries: {str(e)}")
        return []

# Insight operations
def save_insight(dataset_id, name, insight_type, insight_details, importance=None, version_id=None):
    """Save an insight to the database."""
    session = Session()
    try:
        insight_json = json.dumps(insight_details)
        
        # Convert numpy.int64 to regular Python int if needed
        if hasattr(dataset_id, 'item'):
            dataset_id = int(dataset_id)
        
        if version_id is not None and hasattr(version_id, 'item'):
            version_id = int(version_id)
            
        if importance is not None and hasattr(importance, 'item'):
            importance = float(importance)
        
        result = session.execute(
            insights.insert().values(
                dataset_id=dataset_id,
                version_id=version_id,
                name=name,
                type=insight_type,
                insight_json=insight_json,
                importance=importance
            )
        )
        
        session.commit()
        return result.inserted_primary_key[0]
    except Exception as e:
        session.rollback()
        st.error(f"Error saving insight: {str(e)}")
        return None
    finally:
        session.close()

def get_insights(dataset_id, version_id=None):
    """Get insights for a dataset, optionally filtered by version, with retry logic."""
    def _get_insights_operation():
        session = Session()
        try:
            # Convert numpy.int64 to regular Python int if needed
            if hasattr(dataset_id, 'item'):
                dataset_id_int = int(dataset_id)
            else:
                dataset_id_int = dataset_id
                
            # Also convert version_id if provided
            if version_id is not None and hasattr(version_id, 'item'):
                version_id_int = int(version_id)
            else:
                version_id_int = version_id
                
            query = session.query(insights).filter(insights.c.dataset_id == dataset_id_int)
            
            if version_id_int is not None:
                query = query.filter(insights.c.version_id == version_id_int)
            
            results = query.all()
            
            insight_list = [
                {
                    'id': row.id,
                    'name': row.name,
                    'type': row.type,
                    'created_at': row.created_at,
                    'details': json.loads(row.insight_json),
                    'importance': row.importance
                }
                for row in results
            ]
            
            return insight_list
        except Exception as e:
            if not isinstance(e, (OperationalError, SQLAlchemyError)):
                st.error(f"Error retrieving insights: {str(e)}")
            raise
        finally:
            session.close()
    
    try:
        return execute_with_retry(_get_insights_operation)
    except Exception as e:
        st.error(f"Failed to retrieve insights after retries: {str(e)}")
        return []

# User management operations
def create_user(email, password_hash, full_name=None):
    """Create a new user."""
    session = Session()
    try:
        # Check if user already exists
        existing = session.query(users).filter(users.c.email == email).first()
        if existing:
            return {'success': False, 'message': 'Email already exists'}
        
        # Insert new user
        result = session.execute(
            users.insert().values(
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                subscription_tier='free'
            )
        )
        
        session.commit()
        return {'success': True, 'user_id': result.inserted_primary_key[0]}
    except Exception as e:
        session.rollback()
        st.error(f"Error creating user: {str(e)}")
        return {'success': False, 'message': str(e)}
    finally:
        session.close()

def get_user_by_email(email):
    """Get user by email."""
    def _get_user_operation():
        session = Session()
        try:
            result = session.query(users).filter(users.c.email == email).first()
            if result:
                return {
                    'id': result.id,
                    'email': result.email,
                    'password_hash': result.password_hash,
                    'full_name': result.full_name,
                    'created_at': result.created_at,
                    'last_login': result.last_login,
                    'subscription_tier': result.subscription_tier,
                    'subscription_start_date': result.subscription_start_date,
                    'subscription_end_date': result.subscription_end_date,
                    'is_trial': bool(result.is_trial),
                    'trial_start_date': result.trial_start_date,
                    'trial_end_date': result.trial_end_date
                }
            return None
        except Exception as e:
            if not isinstance(e, (OperationalError, SQLAlchemyError)):
                st.error(f"Error retrieving user: {str(e)}")
            raise
        finally:
            session.close()
    
    try:
        return execute_with_retry(_get_user_operation)
    except Exception as e:
        st.error(f"Failed to retrieve user after retries: {str(e)}")
        return None

def get_user_by_id(user_id):
    """Get user by ID."""
    def _get_user_operation():
        session = Session()
        try:
            # Convert numpy.int64 to regular Python int if needed
            if hasattr(user_id, 'item'):
                user_id_int = int(user_id)
            else:
                user_id_int = user_id
                
            result = session.query(users).filter(users.c.id == user_id_int).first()
            if result:
                return {
                    'id': result.id,
                    'email': result.email,
                    'password_hash': result.password_hash,
                    'full_name': result.full_name,
                    'created_at': result.created_at,
                    'last_login': result.last_login,
                    'subscription_tier': result.subscription_tier,
                    'subscription_start_date': result.subscription_start_date,
                    'subscription_end_date': result.subscription_end_date,
                    'is_trial': bool(result.is_trial),
                    'trial_start_date': result.trial_start_date,
                    'trial_end_date': result.trial_end_date
                }
            return None
        except Exception as e:
            if not isinstance(e, (OperationalError, SQLAlchemyError)):
                st.error(f"Error retrieving user: {str(e)}")
            raise
        finally:
            session.close()
    
    try:
        return execute_with_retry(_get_user_operation)
    except Exception as e:
        st.error(f"Failed to retrieve user after retries: {str(e)}")
        return None

def update_user_subscription(user_id, tier, subscription_start_date=None, subscription_end_date=None):
    """Update user subscription tier and dates."""
    session = Session()
    try:
        values = {'subscription_tier': tier}
        
        if subscription_start_date:
            values['subscription_start_date'] = subscription_start_date
        
        if subscription_end_date:
            values['subscription_end_date'] = subscription_end_date
        
        # Convert numpy.int64 to regular Python int if needed
        if hasattr(user_id, 'item'):
            user_id_int = int(user_id)
        else:
            user_id_int = user_id
            
        session.execute(
            users.update().where(users.c.id == user_id_int).values(**values)
        )
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"Error updating user subscription: {str(e)}")
        return False
    finally:
        session.close()

def start_user_trial(user_id, trial_days=7):
    """Start a free trial for a user."""
    session = Session()
    try:
        now = datetime.datetime.utcnow()
        trial_end = now + datetime.timedelta(days=trial_days)
        
        # Convert numpy.int64 to regular Python int if needed
        if hasattr(user_id, 'item'):
            user_id_int = int(user_id)
        else:
            user_id_int = user_id
            
        session.execute(
            users.update().where(users.c.id == user_id_int).values(
                is_trial=1,
                trial_start_date=now,
                trial_end_date=trial_end,
                subscription_tier='pro'
            )
        )
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"Error starting trial: {str(e)}")
        return False
    finally:
        session.close()

def update_last_login(user_id):
    """Update the last login timestamp for a user."""
    session = Session()
    try:
        # Convert numpy.int64 to regular Python int if needed
        if hasattr(user_id, 'item'):
            user_id_int = int(user_id)
        else:
            user_id_int = user_id
            
        session.execute(
            users.update().where(users.c.id == user_id_int).values(
                last_login=datetime.datetime.utcnow()
            )
        )
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"Error updating last login: {str(e)}")
        return False
    finally:
        session.close()

def check_valid_credentials(email, password_hash):
    """Check if email and password combination is valid."""
    user = get_user_by_email(email)
    if user and user['password_hash'] == password_hash:
        return user
    return None

# Password reset functionality
def create_password_reset_token(email):
    """Create a password reset token and store it in the database.
    
    Args:
        email: The email of the user requesting password reset
        
    Returns:
        The token if successful, None otherwise
    """
    user = get_user_by_email(email)
    if not user:
        # Don't reveal if email exists or not for security
        return None
        
    session = Session()
    try:
        # Generate a random token
        token = hashlib.sha256(os.urandom(32)).hexdigest()
        
        # Set expiration time (24 hours from now)
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        
        # Insert the token into the database
        session.execute(
            password_reset_tokens.insert().values(
                user_id=user['id'],
                token=token,
                expires_at=expires_at,
                used=0
            )
        )
        
        session.commit()
        return token
    except Exception as e:
        session.rollback()
        st.error(f"Error creating password reset token: {str(e)}")
        return None
    finally:
        session.close()

def validate_password_reset_token(token):
    """Check if a password reset token is valid and not expired.
    
    Args:
        token: The token to validate
        
    Returns:
        The user_id if valid, None otherwise
    """
    session = Session()
    try:
        # Get the token from the database
        token_record = session.query(password_reset_tokens).filter(
            password_reset_tokens.c.token == token,
            password_reset_tokens.c.used == 0,
            password_reset_tokens.c.expires_at > datetime.datetime.utcnow()
        ).first()
        
        if token_record:
            return token_record.user_id
        return None
    except Exception as e:
        st.error(f"Error validating password reset token: {str(e)}")
        return None
    finally:
        session.close()

def mark_token_as_used(token):
    """Mark a password reset token as used.
    
    Args:
        token: The token to mark as used
        
    Returns:
        True if successful, False otherwise
    """
    session = Session()
    try:
        session.execute(
            password_reset_tokens.update().where(
                password_reset_tokens.c.token == token
            ).values(
                used=1
            )
        )
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"Error marking token as used: {str(e)}")
        return False
    finally:
        session.close()

def update_user_password(user_id, new_password_hash):
    """Update a user's password.
    
    Args:
        user_id: The ID of the user
        new_password_hash: The new password hash
        
    Returns:
        True if successful, False otherwise
    """
    session = Session()
    try:
        # Convert user_id to int if needed
        if hasattr(user_id, 'item'):
            user_id_int = int(user_id)
        else:
            user_id_int = user_id
            
        session.execute(
            users.update().where(users.c.id == user_id_int).values(
                password_hash=new_password_hash
            )
        )
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"Error updating password: {str(e)}")
        return False
    finally:
        session.close()