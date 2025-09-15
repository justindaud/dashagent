# backend/app/routers/user_routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.schemas.response import ApiResponse
from app.controllers import user_controller as ctl
from app.middlewares.middleware import require_admin
from app.model.user import User as UserModel
from app.utils.response import success

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.post("/register", response_model=ApiResponse[UserOut])
def register_user(payload: UserCreate, db: Session = Depends(get_db), _: UserModel = Depends(require_admin)):
    user = ctl.register_user_controller(
        db,
        username=payload.username,
        password=payload.password,
        confirm_password=payload.confirm_password,
        full_name=payload.full_name,
        role_str=payload.role,
    )
    return success(message="User created successfully", data=UserOut.model_validate(user), status_code=201)

@router.get("/", response_model=ApiResponse[UserOut])
def list_users(db: Session = Depends(get_db), _: UserModel = Depends(require_admin)):
    users = ctl.list_users_controller(db)
    return success(message="Users list fetched successfully", data=[UserOut.model_validate(u) for u in users], status_code=200)

@router.get("/{user_id}", response_model=ApiResponse[UserOut])
def get_user_by_id(user_id: str, db: Session = Depends(get_db), _: UserModel = Depends(require_admin)):
    user = ctl.get_user_by_id_controller(db, user_id)
    return success(message="User detail fetched successfully", data=UserOut.model_validate(user), status_code=200)

@router.put("/{user_id}", response_model=ApiResponse[UserOut])
def update_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db), _: UserModel = Depends(require_admin)):
    user = ctl.update_user_controller(
        db,
        target_user_id=user_id,
        username=payload.username,
        full_name=payload.full_name,
        password=payload.password,
        confirm_password=payload.confirm_password,
        role_str=payload.role,
        is_active=payload.is_active,
    )
    return success(message="User updated successfully", data=UserOut.model_validate(user), status_code=200)
