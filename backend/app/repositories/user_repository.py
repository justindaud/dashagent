# backend/app/repositories/user_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from app.model.user import User

def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def username_exists_ci(db: Session, username: str, exclude_user_id: Optional[str] = None) -> bool:
    q = db.query(User).filter(func.upper(User.username) == func.upper(func.trim(username)))
    if exclude_user_id:
        q = q.filter(User.id != exclude_user_id)
    return db.query(q.exists()).scalar()

def list_users(db: Session) -> List[User]:
    return db.query(User).order_by(User.created_at.desc()).all()

def add_user(db: Session, user: User) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user(db: Session, user: User) -> User:
    db.commit()
    db.refresh(user)
    return user
