from app.core.db import SessionLocal
from app.services.auth_service import get_password_hash
from app.models.user import User

def create_admin():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            user = User(
                username="admin",
                email="admin@luse.co.zm",
                hashed_password=get_password_hash("password123")
            )
            db.add(user)
            db.commit()
            print("User 'admin' created successfully.")
        else:
            print("User 'admin' already exists.")
    except Exception as e:
        print(f"Error creating user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
