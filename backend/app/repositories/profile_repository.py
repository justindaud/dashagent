# backend/app/repositories/profile_repository.py
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.model.user import User

def username_exists_ci(db: Session, username: str, exclude_user_id: Optional[str] = None) -> bool:
    q = db.query(User).filter(func.upper(User.username) == func.upper(func.trim(username)))
    if exclude_user_id:
        q = q.filter(User.user_id != exclude_user_id)
    return db.query(q.exists()).scalar()

def update_profile(db: Session, user: User) -> User:
    db.commit()
    db.refresh(user)
    return user
