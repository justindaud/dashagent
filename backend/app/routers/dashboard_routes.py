# app/routers/dashboard_routes.py
import logging
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.dashboard import DashboardStats, RecentUpload
from app.controllers.dashboard_controller import (
    get_dashboard_stats_controller,
    get_recent_uploads_controller,
    get_data_preview_controller,
)
from app.db.clickhouse import get_clickhouse_db
from app.db.database import get_db
from app.model.user import User
from app.middlewares.middleware import get_current_user
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
logger = logging.getLogger(__name__)

@router.get("/stats", response_model=ApiResponse[DashboardStats])
async def get_dashboard_stats(
    db: Session = Depends(get_clickhouse_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[DashboardStats]:
    try:
        stats = await get_dashboard_stats_controller(db)
        return ApiResponse[DashboardStats](
            code=200,
            messages="Dashboard stats fetched successfully",
            data=[stats],
        )
    except Exception as e:
        logger.error("[dashboard_route] Error fetching dashboard stats: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error fetching dashboard stats",
        )


@router.get("/recent-uploads", response_model=ApiResponse[RecentUpload])
async def get_recent_uploads(
    limit: int = 10,
    db_pg: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[RecentUpload]:
    try:
        uploads: List[RecentUpload] = await get_recent_uploads_controller(db_pg, limit=limit)
        return ApiResponse[RecentUpload](
            code=200,
            messages="Recent uploads fetched successfully",
            data=uploads,
        )
    except Exception as e:
        logger.error("[dashboard_route] Error fetching recent uploads: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error fetching recent uploads",
        )

@router.get("/data-preview/{data_type}", response_model=ApiResponse[Dict[str, Any]])
async def get_data_preview(
    data_type: str,
    limit: int = 5,
    db_pg: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[Dict[str, Any]]:
    try:
        data = await get_data_preview_controller(db_pg, data_type=data_type, limit=limit)
        return ApiResponse[Dict[str, Any]](
            code=200,
            messages="Data preview fetched successfully",
            data=data,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid data type")
    except Exception as e:
        logger.error("[dashboard_route] Error fetching data preview: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error fetching data preview",
        )
