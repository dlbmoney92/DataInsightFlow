import os
import hashlib
import streamlit as st
from sqlalchemy import create_engine, text
from utils.database import users, get_user_by_email

# Get database URL from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")

def hash_password(password):
    """Generate a secure hash for the password."""
    salt = "analyticsassist"  # Fixed salt for consistency
    salted_password = password + salt
    return hashlib.sha256(salted_password.encode()).hexdigest()

def update_admin_user():
    """
    Update or create the admin user with specified credentials.
    Email: dariuslbell92@gmail.com
    Password: $Glasses1992
    """
    if not DATABASE_URL:
        st.error("Database URL not found. Please check environment configuration.")
        return False
    
    admin_email = "dariuslbell92@gmail.com"
    admin_password = "$Glasses1992"
    password_hash = hash_password(admin_password)
    
    # Create database engine
    engine = create_engine(DATABASE_URL)
    
    # Check if admin user exists
    existing_user = get_user_by_email(admin_email)
    
    try:
        with engine.connect() as connection:
            if existing_user:
                # Update existing admin user
                print(f"Updating admin user: {admin_email}")
                connection.execute(
                    users.update()
                    .where(users.c.email == admin_email)
                    .values(password_hash=password_hash)
                )
                print("Admin user updated successfully")
            else:
                # Create new admin user
                print(f"Creating admin user: {admin_email}")
                connection.execute(
                    users.insert().values(
                        email=admin_email,
                        password_hash=password_hash,
                        full_name="Admin User",
                        subscription_tier="enterprise",  # Give admin the highest tier
                        is_admin=1  # Set admin flag
                    )
                )
                print("Admin user created successfully")
            
            # Commit the transaction
            connection.commit()
            return True
    except Exception as e:
        print(f"Error updating admin user: {str(e)}")
        return False

if __name__ == "__main__":
    success = update_admin_user()
    if success:
        print("Admin user setup completed successfully")
    else:
        print("Failed to set up admin user")