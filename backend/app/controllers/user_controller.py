# controllers/user_controller.py
import re
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.model.user import User, UserRole
from app.repositories import user_repository as repo
from app.utils.hash import hash_password, verify_password

_NO_SPACE_RE = re.compile(r"^\S+$")
_PASSWORD_RE = re.compile(r"^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9])\S{8,}$")

def _validate_username(username: str) -> None:
    if not _NO_SPACE_RE.match(username):
        raise HTTPException(
            status_code=400,
            detail="Username must not contain spaces"
        )
    if username != username.upper():
        raise HTTPException(
            status_code=400,
            detail="Username must be uppercase"
        )

def _validate_password(password: str, confirm_password: str) -> None:
    if not _NO_SPACE_RE.match(password):
        raise HTTPException(
            status_code=400,
            detail="Password must not contain spaces"
        )
    if not _PASSWORD_RE.match(password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters with 1 uppercase, 1 special character, and 1 number",
        )
    if password != confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Password and confirm password do not match",
        )

def _parse_role(role_str: str) -> UserRole:
    try:
        return UserRole(role_str)
    except Exception:
        raise HTTPException(
            status_code=400, detail="Failed to validate role"
        )

def register_user_controller(db: Session, username: str, password: str, confirm_password: str, full_name: str, role_str: str):
    _validate_username(username)
    _validate_password(password, confirm_password)
    role = _parse_role(role_str)

    if repo.username_exists_ci(db, username):
        raise HTTPException(status_code=400, detail="Username already registered")

    user = User(
        username=username,
        full_name=full_name,
        password=hash_password(password),
        role=role,
        is_active=True,
        token_version=0,
    )
    return repo.add_user(db, user)

def list_users_controller(db: Session):
    return repo.list_users(db)

def get_user_by_id_controller(db: Session, user_id: str):
    user = repo.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def update_user_controller(
    db: Session,
    target_user_id: str,
    username: Optional[str],
    full_name: Optional[str],
    password: Optional[str],
    confirm_password: Optional[str],
    role_str: Optional[str],
    is_active: Optional[bool],
):
    user = repo.get_user_by_id(db, target_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if (
        username is None
        and full_name is None
        and password is None
        and role_str is None
        and is_active is None
    ):
        raise HTTPException(status_code=400, detail="At least one field to update is required")

    bumped = False

    if username is not None:
        username = username.strip()
        _validate_username(username)
        if username.upper() != (user.username or "").upper():
            if repo.username_exists_ci(db, username, exclude_user_id=user.id):
                raise HTTPException(status_code=400, detail="Username already in use")
            user.username = username
            bumped = True

    if full_name is not None:
        full_name = full_name.strip()
        if full_name == "":
            raise HTTPException(status_code=400, detail="full_name is required")
        if full_name != (user.full_name or ""):
            user.full_name = full_name

    if password is not None:
        if confirm_password is None:
            raise HTTPException(status_code=400, detail="Password and confirm password do not match")
        _validate_password(password.strip(), confirm_password.strip())
        if not verify_password(password, user.password):
            user.password = hash_password(password)
            bumped = True

    if role_str is not None:
        role = _parse_role(role_str.strip())
        if role != user.role:
            user.role = role
            bumped = True

    if is_active is not None and bool(is_active) != bool(user.is_active):
        user.is_active = bool(is_active)
        bumped = True

    if bumped:
        user.token_version = (user.token_version or 0) + 1

    return repo.update_user(db, user)
