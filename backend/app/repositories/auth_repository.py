# backend/app/repositories/auth_repository.py
from sqlalchemy.orm import Session
from app.model.user import User

def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()

def bump_token_version(db: Session, user: User) -> User:
    user.token_version = (user.token_version or 0) + 1
    db.commit()
    db.refresh(user)
    return user
