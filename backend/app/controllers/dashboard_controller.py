# app/controllers/dashboard_controller.py
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.model.user import User
from app.schemas.dashboard import DashboardStats, RecentUpload
from app.repositories.dashboard_repository import (
    get_dashboard_stats_repo,
    get_recent_uploads_repo,
    get_data_preview_repo,
)

logger = logging.getLogger(__name__)

async def get_dashboard_stats_controller(db: Session) -> DashboardStats:
    try:
        stats_dict = get_dashboard_stats_repo(db)
        return DashboardStats(**stats_dict)
    except Exception as e:
        logger.error("[dashboard_controller] Error compile dashboard stats: %s", e, exc_info=True)
        raise

async def get_recent_uploads_controller(db_pg: Session, limit: int = 10,) -> List[RecentUpload]:
    try:
        rows = get_recent_uploads_repo(db_pg, limit=limit)
        return [RecentUpload(**row) for row in rows]
    except Exception as e:
        logger.error("[dashboard_controller] Error fetching recent uploads: %s", e, exc_info=True)
        raise

async def get_data_preview_controller(db_pg: Session, data_type: str, limit: int = 5) -> List[Dict[str, Any]]:
    try:
        return get_data_preview_repo(db_pg, data_type=data_type, limit=limit)
    except ValueError as ve:
        logger.warning("[dashboard_controller] Invalid data type for preview: %s", ve)
        raise ve
    except Exception as e:
        logger.error("[dashboard_controller] Error fetching data preview: %s", e, exc_info=True)
        raise