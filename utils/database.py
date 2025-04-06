import os
import json
import datetime
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, LargeBinary, MetaData, Table, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import base64
import io

# Get database URL from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")

# Create SQLAlchemy engine
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    # Provide a fallback for development/testing
    st.warning("Database URL not found. Using in-memory SQLite database for testing.")
    engine = create_engine('sqlite:///:memory:')

# Create base class for declarative models
Base = declarative_base()

# Define metadata object
metadata = MetaData()

# Define tables using SQLAlchemy's Table construct
datasets = Table(
    'datasets', 
    metadata,
    Column('id', Integer, primary_key=True),
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
    
    # Check if tables exist and create them if they don't
    if not inspector.has_table('datasets'):
        metadata.create_all(engine)
        st.success("Database initialized successfully.")
        return True
    return False

# Session factory
Session = sessionmaker(bind=engine)

# DataFrame serialization/deserialization
def serialize_dataframe(df):
    """Serialize a pandas DataFrame to bytes."""
    output = io.BytesIO()
    df.to_parquet(output)
    return output.getvalue()

def deserialize_dataframe(data):
    """Deserialize bytes back to a pandas DataFrame."""
    return pd.read_parquet(io.BytesIO(data))

# Dataset operations
def save_dataset(name, description, file_name, file_type, df, column_types):
    """Save a dataset to the database."""
    session = Session()
    try:
        serialized_data = serialize_dataframe(df)
        column_types_json = json.dumps(column_types)
        
        # Check if dataset with same name exists
        existing = session.query(datasets).filter(datasets.c.name == name).first()
        
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
                    column_count=df.shape[1]
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
                    column_count=df.shape[1]
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

def get_dataset(dataset_id):
    """Retrieve a dataset from the database."""
    session = Session()
    try:
        result = session.query(datasets).filter(datasets.c.id == dataset_id).first()
        
        if result:
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
                'column_count': result.column_count
            }
        return None
    except Exception as e:
        st.error(f"Error retrieving dataset: {str(e)}")
        return None
    finally:
        session.close()

def list_datasets():
    """List all datasets in the database."""
    session = Session()
    try:
        results = session.query(datasets).all()
        
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
                'column_count': row.column_count
            }
            for row in results
        ]
        
        return dataset_list
    except Exception as e:
        st.error(f"Error listing datasets: {str(e)}")
        return []
    finally:
        session.close()

def delete_dataset(dataset_id):
    """Delete a dataset and all related records."""
    session = Session()
    try:
        # Delete related records first
        session.execute(transformations.delete().where(transformations.c.dataset_id == dataset_id))
        session.execute(versions.delete().where(versions.c.dataset_id == dataset_id))
        session.execute(insights.delete().where(insights.c.dataset_id == dataset_id))
        
        # Delete the dataset
        session.execute(datasets.delete().where(datasets.c.id == dataset_id))
        
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
    """Get all transformations for a dataset."""
    session = Session()
    try:
        results = session.query(transformations).filter(transformations.c.dataset_id == dataset_id).all()
        
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
        st.error(f"Error retrieving transformations: {str(e)}")
        return []
    finally:
        session.close()

# Version operations
def save_version(dataset_id, version_number, name, description, df, transformations_applied):
    """Save a version of a dataset."""
    session = Session()
    try:
        serialized_data = serialize_dataframe(df)
        transformations_json = json.dumps(transformations_applied)
        
        result = session.execute(
            versions.insert().values(
                dataset_id=dataset_id,
                version_number=version_number,
                name=name,
                description=description,
                data=serialized_data,
                transformations_applied=transformations_json,
                row_count=df.shape[0],
                column_count=df.shape[1]
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
    """Get a specific version."""
    session = Session()
    try:
        result = session.query(versions).filter(versions.c.id == version_id).first()
        
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
        st.error(f"Error retrieving version: {str(e)}")
        return None
    finally:
        session.close()

def get_versions(dataset_id):
    """Get all versions for a dataset."""
    session = Session()
    try:
        results = session.query(versions).filter(versions.c.dataset_id == dataset_id).all()
        
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
        st.error(f"Error retrieving versions: {str(e)}")
        return []
    finally:
        session.close()

# Insight operations
def save_insight(dataset_id, name, insight_type, insight_details, importance=None, version_id=None):
    """Save an insight to the database."""
    session = Session()
    try:
        insight_json = json.dumps(insight_details)
        
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
    """Get insights for a dataset, optionally filtered by version."""
    session = Session()
    try:
        query = session.query(insights).filter(insights.c.dataset_id == dataset_id)
        
        if version_id is not None:
            query = query.filter(insights.c.version_id == version_id)
        
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
        st.error(f"Error retrieving insights: {str(e)}")
        return []
    finally:
        session.close()