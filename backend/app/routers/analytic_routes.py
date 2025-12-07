# app/routers/analytics_routes.py
import logging
from datetime import date, datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.controllers.analytics_controller import (
    get_dimensions_controller,
    get_aggregate_controller,
)
from app.db.clickhouse import get_clickhouse_db
from app.db.database import get_db
from app.middlewares.middleware import get_current_user, require_manager
from app.model.user import User
from app.schemas.response import ApiResponse
from app.schemas.analytics import DimensionsResponse, AggregateResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)

@router.get(
    "/dimensions",
    response_model=ApiResponse[DimensionsResponse],
    summary="Get unique dimension values within stay date range",
)
def get_dimensions(
    start: str = Query(..., description="Start date YYYY-MM-DD (inclusive)"),
    end: str = Query(..., description="End date YYYY-MM-DD (inclusive)"),
    db: Session = Depends(get_clickhouse_db),
    current_user: User = Depends(require_manager),
) -> ApiResponse[DimensionsResponse]:
    try:
        start_dt: date = datetime.fromisoformat(start).date()
        end_dt: date = datetime.fromisoformat(end).date()
        if end_dt < start_dt:
            raise HTTPException(status_code=400, detail="end must be on or after start")

        dims = get_dimensions_controller(db=db, start=start_dt, end=end_dt)

        return ApiResponse[DimensionsResponse](
            code=200,
            messages="Data dimensions fetched successfully",
            data=[dims],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching dimensions")
        raise HTTPException(status_code=500, detail=f"Error fetching dimensions: {str(e)}")


@router.get(
    "/aggregate",
    response_model=ApiResponse[AggregateResponse],
    summary="Get aggregated occupancy & revenue analytics",
)
def get_aggregate(
    start: str = Query(..., description="Start date YYYY-MM-DD"),
    end: str = Query(..., description="End date YYYY-MM-DD"),
    group_by: str = Query(
        "none",
        regex="^(none|segment|room_type_desc|local_region|nationality|age_group)$",
        description="Aggregation dimension",
    ),
    segment_in: Optional[str] = Query(None, description="Comma-separated list of segments"),
    room_type_desc_in: Optional[str] = Query(None, description="Comma-separated list of room types"),
    local_region_in: Optional[str] = Query(None, description="Comma-separated list of local regions"),
    nationality_in: Optional[str] = Query(None, description="Comma-separated list of nationalities"),
    top_n: Optional[int] = Query(None, ge=1, le=50),
    include_other: bool = Query(False),
    db_ch: Session = Depends(get_clickhouse_db),
    db_pg: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
) -> ApiResponse[AggregateResponse]:
    try:
        start_dt = datetime.fromisoformat(start).date()
        end_dt = datetime.fromisoformat(end).date()
        if end_dt < start_dt:
            raise HTTPException(status_code=400, detail="end must be on or after start")

        agg_dict = get_aggregate_controller(
            db_ch=db_ch,
            db_pg=db_pg,
            start=start_dt,
            end=end_dt,
            group_by=group_by,
            segment_in=segment_in,
            room_type_desc_in=room_type_desc_in,
            local_region_in=local_region_in,
            nationality_in=nationality_in,
            top_n=top_n,
            include_other=include_other,
        )

        agg = AggregateResponse(**agg_dict)

        return ApiResponse[AggregateResponse](
            code=200,
            messages="Data aggregate fetched successfully",
            data=[agg],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error computing analytics")
        raise HTTPException(status_code=500, detail=f"Error computing analytics: {str(e)}")
