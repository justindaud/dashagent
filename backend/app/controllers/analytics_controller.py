# app/controllers/analytics_controller.py
import logging
from datetime import date
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.repositories.analytics_repository import get_dimensions, get_aggregate_clickhouse
from app.schemas.analytics import DimensionsResponse
from app.controllers.room_build_controller import get_room_count_until_date_controller

logger = logging.getLogger(__name__)


def get_dimensions_controller(db: Session, start: date, end: date) -> DimensionsResponse:
    raw = get_dimensions(db, start, end)
    return DimensionsResponse(**raw)


def _fetch_room_count_from_pg(db_pg: Session, target_date: date) -> int:
    try:
        return get_room_count_until_date_controller(db_pg, target_date)
    except Exception as e:
        logger.error("Failed to fetch room_count from Postgres: %s", e, exc_info=True)
        return 0


def get_aggregate_controller(
    db_ch: Session,
    db_pg: Session,
    start: date,
    end: date,
    group_by: str,
    segment_in: Optional[str],
    room_type_desc_in: Optional[str],
    local_region_in: Optional[str],
    nationality_in: Optional[str],
    top_n: Optional[int],
    include_other: bool,
    room_count_override: Optional[int],
) -> Dict[str, Any]:
    base_result = get_aggregate_clickhouse(
        db=db_ch,
        start=start,
        end=end,
        group_by=group_by,
        segment_in=segment_in,
        room_type_desc_in=room_type_desc_in,
        local_region_in=local_region_in,
        nationality_in=nationality_in,
    )

    items = base_result.get("breakdown", [])

    if room_count_override is not None and room_count_override > 0:
        room_count = room_count_override
    else:
        room_count = _fetch_room_count_from_pg(db_pg, start)

    totals = base_result.get("totals", {}) or {}
    raw_room_sold = totals.get("room_sold", 0) or 0

    if room_count > 0:
        room_sold_per_room = float(raw_room_sold) / float(room_count)
    else:
        room_sold_per_room = 0.0

    totals["room_count"] = room_count
    totals["room_sold_per_room"] = room_sold_per_room
    base_result["totals"] = totals

    if group_by == "none":
        base_result["breakdown"] = []
    else:
        if top_n is not None and top_n > 0 and len(items) > top_n:
            items_sorted = sorted(items, key=lambda x: x["revenue_sum"], reverse=True)
            head = items_sorted[:top_n]
            tail = items_sorted[top_n:]

            if include_other and tail:
                other = {
                    "key": "Other",
                    "revenue_sum": float(sum(x["revenue_sum"] for x in tail)),
                    "room_sold": int(sum(x["room_sold"] for x in tail)),
                    "arr_simple": 0.0,
                    "bookings_count": int(sum(x["bookings_count"] for x in tail)),
                }
                head = head + [other]

            base_result["breakdown"] = head
        else:
            base_result["breakdown"] = items

    normalized_breakdown = []
    for item in base_result.get("breakdown", []):
        rs = item.get("room_sold", 0) or 0
        if room_count > 0:
            rs_per_room = float(rs) / float(room_count)
        else:
            rs_per_room = 0.0

        item["room_sold_per_room"] = rs_per_room
        normalized_breakdown.append(item)

    base_result["breakdown"] = normalized_breakdown

    return base_result
