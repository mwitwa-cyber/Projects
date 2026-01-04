import sys
import os

# Add the parent directory to sys.path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db import SessionLocal
from app.models.user import User
from app.services.auth_service import get_password_hash

def create_user():
    db = SessionLocal()
    try:
        username = "admin"
        email = "admin@luse.co.zm"
        password = "Password123!"
        
        # Check if user exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"User '{username}' already exists.")
            # Update password
            existing_user.hashed_password = get_password_hash(password)
            db.commit()
            print(f"Password updated for '{username}' to '{password}'")
            return

        hashed_password = get_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password
        )
        
        db.add(new_user)
        db.commit()
        print(f"User '{username}' created successfully.")
        print(f"Password: {password}")
        
    except Exception as e:
        print(f"Error creating user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_user()
