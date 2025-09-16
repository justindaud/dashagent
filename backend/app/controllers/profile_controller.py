# backend/app/controllers/profile_controller.py
import re
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.model.user import User
from app.repositories import profile_repository as repo
from app.utils.hash import hash_password, verify_password

_NO_SPACE_RE = re.compile(r"^\S+$")
_PASSWORD_RE = re.compile(r"^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9])\S{8,}$")

def _require_at_least_one(username, password, full_name):
    if (
        (username is None or str(username).strip() == "") and
        (password is None or str(password).strip() == "") and
        (full_name is None or str(full_name).strip() == "")
    ):
        raise HTTPException(status_code=400, detail="At least one of username, password, or full_name is required")

def _validate_username(username: str) -> None:
    if not _NO_SPACE_RE.match(username):
        raise HTTPException(status_code=400, detail="Username must not contain spaces")
    if username != username.upper():
        raise HTTPException(status_code=400, detail="Username must be uppercase")

def _validate_password(password: str, confirm_password: str) -> None:
    if not _NO_SPACE_RE.match(password):
        raise HTTPException(status_code=400, detail="Password must not contain spaces")
    if not _PASSWORD_RE.match(password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters with 1 uppercase, 1 special character, and 1 number",
        )
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Password and confirm password do not match")

def profile_controller(current_user: User) -> dict:
    return {
        "user_id": str(current_user.user_id),
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
    }

def update_profile_controller(
    db: Session,
    current_user: User,
    *,
    username: str | None,
    password: str | None,
    confirm_password: str | None,
    full_name: str | None,
) -> dict:
    _require_at_least_one(username, password, full_name)

    bumped = False

    if username is not None:
        username = username.strip()
        _validate_username(username)

        if username.upper() != (current_user.username or "").upper():
            if repo.username_exists_ci(db, username, exclude_user_id=current_user.user_id):
                raise HTTPException(status_code=400, detail="Username already in use")
            current_user.username = username
            bumped = True

    if password is not None:
        password = password.strip()
        _validate_password(password, confirm_password)

        if not verify_password(password, current_user.password):
            current_user.password = hash_password(password)
            bumped = True

    if full_name is not None:
        full_name = full_name.strip()
        if full_name == "":
            raise HTTPException(status_code=400, detail="full_name is required")
        if full_name != (current_user.full_name or ""):
            current_user.full_name = full_name

    if bumped:
        current_user.token_version = (current_user.token_version or 0) + 1

    repo.update_profile(db, current_user)

    return {
        "message": ("Profile updated successfully — please login again" if bumped else "Profile updated successfully"),
        "user_id": str(current_user.user_id),
    }