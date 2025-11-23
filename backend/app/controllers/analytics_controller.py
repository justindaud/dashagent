# app/controllers/analytics_controller.py
import logging
from datetime import date, timedelta
from typing import Any, Dict, Optional, List, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.repositories.analytics_repository import (
    get_dimensions,
    get_aggregate_clickhouse,
    get_nightly_totals_per_type_clickhouse,
)
from app.schemas.analytics import DimensionsResponse
from app.utils.common import parse_csv_list
from app.model.room import RoomBuild

logger = logging.getLogger(__name__)


def get_dimensions_controller(db: Session, start: date, end: date) -> DimensionsResponse:
    raw = get_dimensions(db, start, end)
    return DimensionsResponse(**raw)


def _fetch_room_counts_map_from_pg_for_date(
    db_pg: Session,
    target_date: date,
    room_type_desc_filter: Optional[List[str]],
) -> Dict[str, int]:
    subq = (
        db_pg.query(
            RoomBuild.room_type_desc.label("room_type_desc"),
            func.max(RoomBuild.built_date).label("max_date"),
        )
        .filter(RoomBuild.built_date <= target_date)
    )

    if room_type_desc_filter:
        subq = subq.filter(RoomBuild.room_type_desc.in_(room_type_desc_filter))

    subq = subq.group_by(RoomBuild.room_type_desc).subquery()

    rows = (
        db_pg.query(
            subq.c.room_type_desc.label("room_type_desc"),
            func.max(RoomBuild.room_count).label("room_count"),
        )
        .join(
            RoomBuild,
            and_(
                RoomBuild.room_type_desc == subq.c.room_type_desc,
                RoomBuild.built_date == subq.c.max_date,
            ),
        )
        .group_by(subq.c.room_type_desc)
        .all()
    )

    result: Dict[str, int] = {}
    for r in rows:
        rt = r.room_type_desc
        cnt = int(r.room_count or 0)
        result[rt] = cnt

    return result


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

    period = base_result.get("period", {}) or {}
    totals_raw = base_result.get("totals", {}) or {}
    breakdown_raw: List[Dict[str, Any]] = base_result.get("breakdown", []) or []

    nights = int(period.get("nights", (end - start).days) or 0)

    total_room_sold = int(totals_raw.get("room_sold", 0) or 0)
    total_revenue = float(totals_raw.get("revenue_sum", 0.0) or 0.0)
    total_bookings = int(totals_raw.get("bookings_count", 0) or 0)

    date_list: List[date] = []
    if nights > 0:
        for i in range(nights):
            date_list.append(start + timedelta(days=i))

    room_type_filter_list: List[str] = parse_csv_list(room_type_desc_in)

    if not room_type_filter_list and group_by == "room_type_desc":
        room_type_filter_list = [b["key"] for b in breakdown_raw if b.get("key")]

    room_count_by_date_and_type: Dict[date, Dict[str, int]] = {}
    room_count_total_per_type: Dict[str, int] = {}

    for d in date_list:
        m = _fetch_room_counts_map_from_pg_for_date(
            db_pg=db_pg,
            target_date=d,
            room_type_desc_filter=room_type_filter_list or None,
        )
        room_count_by_date_and_type[d] = m
        for rt, cnt in m.items():
            room_count_total_per_type[rt] = room_count_total_per_type.get(rt, 0) + (cnt or 0)

    total_room_count_from_pg = (
        sum(room_count_total_per_type.values()) if room_count_total_per_type else 0
    )

    nightly_rows = get_nightly_totals_per_type_clickhouse(
        db=db_ch,
        start=start,
        end=end,
        segment_in=segment_in,
        room_type_desc_in=room_type_desc_in,
        local_region_in=local_region_in,
        nationality_in=nationality_in,
    )

    nightly_sales: Dict[date, Dict[str, Dict[str, Any]]] = {}
    for r in nightly_rows:
        d = r["stay_date"]
        rt = r["room_type_desc"]
        rs = int(r["room_sold"] or 0)
        rv = float(r["revenue_sum"] or 0.0)
        if d not in nightly_sales:
            nightly_sales[d] = {}
        nightly_sales[d][rt] = {
            "room_sold": rs,
            "revenue_sum": rv,
        }

    nightly_total_occ_sum = 0.0
    nightly_total_adr_sum = 0.0

    for d in date_list:
        type_counts = room_count_by_date_and_type.get(d, {})
        sales_for_day = nightly_sales.get(d, {})

        total_room_count_day = sum(type_counts.values()) if type_counts else 0
        total_room_sold_day = 0
        total_revenue_day = 0.0

        for stats in sales_for_day.values():
            total_room_sold_day += int(stats.get("room_sold", 0) or 0)
            total_revenue_day += float(stats.get("revenue_sum", 0.0) or 0.0)

        if total_room_count_day > 0:
            occ_day = float(total_room_sold_day) / float(total_room_count_day)
        else:
            occ_day = 0.0

        if total_room_sold_day > 0:
            adr_day = float(total_revenue_day) / float(total_room_sold_day)
        else:
            adr_day = 0.0

        nightly_total_occ_sum += occ_day
        nightly_total_adr_sum += adr_day

    def _compute_occ_and_adr_sums_for_type(rt: str) -> Tuple[float, float]:
        occ_sum_type = 0.0
        adr_sum_type = 0.0

        if nights <= 0:
            return 0.0, 0.0

        for d in date_list:
            room_count_map = room_count_by_date_and_type.get(d, {})
            cnt_day_type = room_count_map.get(rt, 0) or 0

            stats_map = nightly_sales.get(d, {})
            stats_type = stats_map.get(rt, {"room_sold": 0, "revenue_sum": 0.0})
            rs_day_type = int(stats_type.get("room_sold", 0) or 0)
            rv_day_type = float(stats_type.get("revenue_sum", 0.0) or 0.0)

            if cnt_day_type > 0:
                occ_type_day = float(rs_day_type) / float(cnt_day_type)
            else:
                occ_type_day = 0.0

            if rs_day_type > 0:
                adr_type_day = float(rv_day_type) / float(rs_day_type)
            else:
                adr_type_day = 0.0

            occ_sum_type += occ_type_day
            adr_sum_type += adr_type_day

        return occ_sum_type, adr_sum_type

    enriched_breakdown: List[Dict[str, Any]] = []

    for item in breakdown_raw:
        key = item.get("key")
        room_sold = int(item.get("room_sold", 0) or 0)
        revenue = float(item.get("revenue_sum", 0.0) or 0.0)
        bookings_count = int(item.get("bookings_count", 0) or 0)

        if group_by == "room_type_desc":
            room_count_for_key = room_count_total_per_type.get(key, 0)

            occ_sum_key, adr_sum_key = _compute_occ_and_adr_sums_for_type(key)

            if room_count_for_key > 0:
                occ_key = float(room_sold) / float(room_count_for_key)
            else:
                occ_key = 0.0

            if room_sold > 0:
                arr_key = float(revenue) / float(room_sold)
            else:
                arr_key = 0.0

            avg_occ_key = occ_sum_key

            adr_key = adr_sum_key
        else:
            room_count_for_key = total_room_count_from_pg
            if total_room_count_from_pg > 0:
                occ_key = float(room_sold) / float(total_room_count_from_pg)
            else:
                occ_key = 0.0

            avg_occ_key = occ_key

            if room_sold > 0:
                arr_key = float(revenue) / float(room_sold)
            else:
                arr_key = 0.0

            adr_key = arr_key

        enriched_breakdown.append(
            {
                "key": key,
                "room_sold": room_sold,
                "bookings_count": bookings_count,
                "room_count": room_count_for_key,
                "revenue_sum": revenue,
                "occupancy_rate": occ_key,
                "average_occupancy_rate": avg_occ_key,
                "arr_simple": arr_key,
                "adr_simple": adr_key,
            }
        )

    final_breakdown: List[Dict[str, Any]] = enriched_breakdown

    if group_by != "none":
        if top_n is not None and top_n > 0 and len(enriched_breakdown) > top_n:
            sorted_items = sorted(
                enriched_breakdown,
                key=lambda x: x.get("revenue_sum", 0.0),
                reverse=True,
            )
            head = sorted_items[:top_n]
            tail = sorted_items[top_n:]

            if include_other and tail:
                other_room_sold = sum(t["room_sold"] for t in tail)
                other_bookings = sum(t["bookings_count"] for t in tail)
                other_revenue = sum(t["revenue_sum"] for t in tail)
                other_room_count = sum(t["room_count"] for t in tail)

                if other_room_count > 0:
                    other_occ = float(other_room_sold) / float(other_room_count)
                else:
                    other_occ = 0.0

                if other_room_sold > 0:
                    other_arr = float(other_revenue) / float(other_room_sold)
                else:
                    other_arr = 0.0

                other_item = {
                    "key": "Other",
                    "room_sold": other_room_sold,
                    "bookings_count": other_bookings,
                    "room_count": other_room_count,
                    "revenue_sum": other_revenue,
                    "occupancy_rate": other_occ,
                    "average_occupancy_rate": other_occ,
                    "arr_simple": other_arr,
                    "adr_simple": other_arr,
                }
                final_breakdown = head + [other_item]
            else:
                final_breakdown = head
        else:
            final_breakdown = enriched_breakdown
    else:
        final_breakdown = []

    if final_breakdown:
        total_room_sold = sum(item["room_sold"] for item in final_breakdown)
        total_bookings = sum(item["bookings_count"] for item in final_breakdown)
        total_room_count = sum(item["room_count"] for item in final_breakdown)
        total_revenue = sum(item["revenue_sum"] for item in final_breakdown)
    else:
        total_room_count = total_room_count_from_pg

    if total_room_count > 0:
        occupancy_rate_total = float(total_room_sold) / float(total_room_count)
    else:
        occupancy_rate_total = 0.0

    average_occupancy_rate_total = nightly_total_occ_sum if nights > 0 else 0.0

    adr_simple_total = nightly_total_adr_sum if nights > 0 else 0.0

    if total_room_sold > 0:
        arr_simple_total = float(total_revenue) / float(total_room_sold)
    else:
        arr_simple_total = 0.0

    base_result["totals"] = {
        "room_sold": total_room_sold,
        "bookings_count": total_bookings,
        "room_count": total_room_count,
        "revenue_sum": total_revenue,
        "occupancy_rate": occupancy_rate_total,
        "average_occupancy_rate": average_occupancy_rate_total,
        "arr_simple": arr_simple_total,
        "adr_simple": adr_simple_total,
    }

    base_result["breakdown"] = final_breakdown

    return base_result
