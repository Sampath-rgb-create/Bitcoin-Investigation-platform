import os
import sys

from pathlib import Path

# Ensure repository root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.db.session import SessionLocal, init_db
from backend.app.db.models import User
from backend.app.core.security import get_password_hash


def seed_admin_user(
    username: str = "admin",
    password: str = "InvestigateBTC2026!",
    role: str = "admin",
):
    print("Initializing database tables...")
    init_db()

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"User '{username}' already exists. Updating password hash...")
            existing.password_hash = get_password_hash(password)
            existing.role = role
            existing.active = 1
            db.commit()
            print(f"User '{username}' updated successfully.")
            return existing

        print(f"Creating default {role} user: '{username}'...")
        user = User(
            username=username,
            password_hash=get_password_hash(password),
            role=role,
            active=1,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Default user '{username}' (role={role}) created with ID: {user.id}")
        return user
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin_user()
