from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, text, cast, Date
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.database import get_db
from app.models import ReservasiProcessed


router = APIRouter(prefix="/analytics", tags=["analytics"])


def parse_csv_list(value: Optional[str]) -> Optional[List[str]]:
    if value is None or value == "":
        return None
    # Split by comma, trim spaces, drop empties, keep case as-is (assume upstream normalized)
    return [item.strip() for item in value.split(",") if item.strip()]


@router.get("/aggregate")
def get_aggregate(
    start: str = Query(..., description="Start date YYYY-MM-DD"),
    end: str = Query(..., description="End date YYYY-MM-DD (exclusive end boundary is handled by overlap check)"),
    group_by: str = Query("none", regex="^(none|segment|room_type|local_region|nationality|age_group)$"),
    segment_in: Optional[str] = Query(None, description="Comma-separated list"),
    segment_not_in: Optional[str] = Query(None, description="Comma-separated list"),
    room_type_in: Optional[str] = Query(None, description="Comma-separated list"),
    local_region_in: Optional[str] = Query(None, description="Comma-separated list of cities/regions"),
    nationality_in: Optional[str] = Query(None, description="Comma-separated list"),
    top_n: Optional[int] = Query(None, ge=1, le=50),
    include_other: bool = Query(False),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        if end_dt < start_dt:
            raise HTTPException(status_code=400, detail="end must be on or after start")

        # Base overlap filter: arrival < end AND depart > start
        query = db.query(ReservasiProcessed).filter(
            cast(ReservasiProcessed.arrival_date, Date) < end_dt,
            cast(ReservasiProcessed.depart_date, Date) > start_dt,
        )

        # Apply filters
        seg_in = parse_csv_list(segment_in)
        seg_not_in = parse_csv_list(segment_not_in)
        rt_in = parse_csv_list(room_type_in)
        lr_in = parse_csv_list(local_region_in)
        nat_in = parse_csv_list(nationality_in)

        if seg_in:
            query = query.filter(ReservasiProcessed.segment.in_(seg_in))
        if seg_not_in:
            query = query.filter(~ReservasiProcessed.segment.in_(seg_not_in))
        if rt_in:
            query = query.filter(ReservasiProcessed.room_type.in_(rt_in))
        if lr_in:
            query = query.filter(ReservasiProcessed.local_region.in_(lr_in))
        if nat_in:
            query = query.filter(ReservasiProcessed.nationality.in_(nat_in))

        # Calculate proportional revenue and nights based on overlap
        # This ensures we only count revenue for nights that fall within the filter period
        overlap_nights_expr = func.greatest(
            0,
            func.least(
                func.extract('day', func.least(cast(ReservasiProcessed.depart_date, Date), end_dt) - func.greatest(cast(ReservasiProcessed.arrival_date, Date), start_dt)),
                ReservasiProcessed.nights
            )
        )
        
        revenue_expr = (ReservasiProcessed.room_rate * overlap_nights_expr)
        occupied_nights_expr = func.coalesce(overlap_nights_expr, 0)
        arr_expr = func.avg(ReservasiProcessed.room_rate)
        bookings_expr = func.count(ReservasiProcessed.id)

        totals_row = query.with_entities(
            func.coalesce(func.sum(revenue_expr), 0).label("revenue_sum"),
            func.coalesce(func.sum(occupied_nights_expr), 0).label("occupied_room_nights"),
            func.coalesce(arr_expr, 0).label("arr_simple"),
            bookings_expr.label("bookings_count"),
        ).one()

        period_days = (end_dt.date() - start_dt.date()).days

        result: Dict[str, Any] = {
            "period": {"start": start, "end": end, "days": period_days},
            "totals": {
                "revenue_sum": float(totals_row.revenue_sum or 0),
                "occupied_room_nights": int(totals_row.occupied_room_nights or 0),
                "arr_simple": float(totals_row.arr_simple or 0),
                "bookings_count": int(totals_row.bookings_count or 0),
            },
            "breakdown": [],
        }

        # Breakdown
        if group_by != "none":
            if group_by == "age_group":
                group_key = case(
                    (ReservasiProcessed.age < 18, "unidentified"),
                    (ReservasiProcessed.age.between(18, 24), "18-24"),
                    (ReservasiProcessed.age.between(25, 34), "25-34"),
                    (ReservasiProcessed.age.between(35, 44), "35-44"),
                    (ReservasiProcessed.age.between(45, 54), "45-54"),
                    (ReservasiProcessed.age.between(55, 64), "55-64"),
                    else_="65+",
                ).label("group_key")
            elif group_by == "segment":
                group_key = ReservasiProcessed.segment.label("group_key")
            elif group_by == "room_type":
                group_key = ReservasiProcessed.room_type.label("group_key")
            elif group_by == "local_region":
                group_key = ReservasiProcessed.local_region.label("group_key")
            elif group_by == "nationality":
                group_key = ReservasiProcessed.nationality.label("group_key")
            else:
                raise HTTPException(status_code=400, detail="Invalid group_by")

            breakdown_rows = query.with_entities(
                group_key,
                func.coalesce(func.sum(revenue_expr), 0).label("revenue_sum"),
                func.coalesce(func.sum(occupied_nights_expr), 0).label("occupied_room_nights"),
                func.coalesce(func.avg(ReservasiProcessed.room_rate), 0).label("arr_simple"),
                func.count(ReservasiProcessed.id).label("bookings_count"),
            ).group_by(group_key).all()

            items = [
                {
                    "key": (row.group_key or "Unknown"),
                    "revenue_sum": float(row.revenue_sum or 0),
                    "occupied_room_nights": int(row.occupied_room_nights or 0),
                    "arr_simple": float(row.arr_simple or 0),
                    "bookings_count": int(row.bookings_count or 0),
                }
                for row in breakdown_rows
            ]

            # Optional Top-N handling for pie charts
            if top_n is not None and top_n > 0 and len(items) > top_n:
                items_sorted = sorted(items, key=lambda x: x["revenue_sum"], reverse=True)
                head = items_sorted[:top_n]
                tail = items_sorted[top_n:]
                if include_other and tail:
                    other = {
                        "key": "Other",
                        "revenue_sum": float(sum(x["revenue_sum"] for x in tail)),
                        "occupied_room_nights": int(sum(x["occupied_room_nights"] for x in tail)),
                        "arr_simple": 0.0,  # not meaningful for aggregated other
                        "bookings_count": int(sum(x["bookings_count"] for x in tail)),
                    }
                    result["breakdown"] = head + [other]
                else:
                    result["breakdown"] = head
            else:
                result["breakdown"] = items

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing analytics: {str(e)}")


@router.get("/dimensions")
def get_dimensions(
    start: Optional[str] = Query(None, description="Optional start date YYYY-MM-DD to filter overlap"),
    end: Optional[str] = Query(None, description="Optional end date YYYY-MM-DD to filter overlap"),
    db: Session = Depends(get_db),
) -> Dict[str, List[str]]:
    try:
        query = db.query(ReservasiProcessed)
        if start and end:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            if end_dt <= start_dt:
                raise HTTPException(status_code=400, detail="end must be after start")
            query = query.filter(
                cast(ReservasiProcessed.arrival_date, Date) < end_dt,
                cast(ReservasiProcessed.depart_date, Date) > start_dt,
            )

        # Distinct values per dimension
        def distinct_values(column) -> List[str]:
            rows = query.with_entities(column).filter(column.isnot(None)).distinct().order_by(column.asc()).all()
            return [r[0] for r in rows if r[0] not in (None, '')]

        return {
            "segment": distinct_values(ReservasiProcessed.segment),
            "room_type": distinct_values(ReservasiProcessed.room_type),
            "local_region": distinct_values(ReservasiProcessed.local_region),
            "nationality": distinct_values(ReservasiProcessed.nationality),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dimensions: {str(e)}")


