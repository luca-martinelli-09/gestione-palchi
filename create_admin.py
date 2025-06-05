#!/usr/bin/env python3
"""
Script to create a default admin user for the application.
Run this after setting up the database.
"""

from sqlalchemy.orm import Session
from app.database.base import engine, get_db
from app.models.auth import User
from app.core.auth import get_password_hash


def create_admin_user():
    """Create a default admin user."""
    db = next(get_db())
    
    # Check if admin user already exists
    existing_user = db.query(User).filter(User.username == "admin").first()
    if existing_user:
        print("Admin user already exists!")
        return
    
    # Create admin user
    admin_user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),  # Change this password!
        is_active=True,
        is_superuser=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    print(f"Admin user created successfully!")
    print(f"Username: admin")
    print(f"Password: admin123")
    print(f"Email: admin@example.com")
    print("\n*** IMPORTANT: Please change the default password after first login! ***")


if __name__ == "__main__":
    create_admin_user()