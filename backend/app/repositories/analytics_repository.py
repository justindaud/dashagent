# app/repositories/analytics_repository.py
from datetime import date
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.utils.common import parse_csv_list

_DIMENSION_SQL_TEMPLATE = """
WITH
    toDate(:d_start) AS d_start,
    toDate(:d_end)   AS d_end
SELECT
    DISTINCT value
FROM
(
    SELECT
        {dimension} AS value,
        greatest(arrival_date, d_start) AS overlap_start,
        least(depart_date,  d_end)      AS overlap_end
    FROM default.datamart_reservations final
    WHERE
        arrival_date <= d_end
        AND depart_date  >= d_start
) AS r
ARRAY JOIN
    arrayMap(
        x -> r.overlap_start + x,
        range(dateDiff('day', r.overlap_start, r.overlap_end) + 1)
    ) AS day
WHERE
    value IS NOT NULL
    AND value != ''
ORDER BY
    value
"""


def _fetch_dimension_values(
    db: Session,
    dimension: str,
    start: date,
    end: date,
) -> List[str]:
    sql = text(_DIMENSION_SQL_TEMPLATE.format(dimension=dimension))
    rows = db.execute(sql, {"d_start": start, "d_end": end}).all()
    return [r[0] for r in rows]


def get_dimensions(
    db: Session,
    start: date,
    end: date,
) -> Dict[str, Any]:
    return {
        "segment": _fetch_dimension_values(db, "segment", start, end),
        "nationality": _fetch_dimension_values(db, "nationality", start, end),
        "local_region": _fetch_dimension_values(db, "local_region", start, end),
        "room_type_desc": _fetch_dimension_values(db, "room_type_desc", start, end),
    }

def _build_in_filter(column: str, values: List[str]) -> str:
    if not values:
        return ""
    escaped = [v.replace("'", "''") for v in values]
    values_sql = ",".join(f"'{v}'" for v in escaped)
    return f" AND {column} IN ({values_sql})\n"


def _get_group_key_expr(group_by: str) -> Optional[str]:
    if group_by == "segment":
        return "ifNull(segment, 'Unknown')"
    if group_by == "room_type_desc":
        return "ifNull(room_type_desc, 'Unknown')"
    if group_by == "local_region":
        return "ifNull(local_region, 'Unknown')"
    if group_by == "nationality":
        return "ifNull(nationality, 'Unknown')"
    if group_by == "age_group":
        return (
            "multiIf("
            "age < 18, 'unidentified',"
            "age BETWEEN 18 AND 24, '18-24',"
            "age BETWEEN 25 AND 34, '25-34',"
            "age BETWEEN 35 AND 44, '35-44',"
            "age BETWEEN 45 AND 54, '45-54',"
            "age BETWEEN 55 AND 64, '55-64',"
            "'65+'"
            ")"
        )
    return None


def get_aggregate_clickhouse(
    db: Session,
    start: date,
    end: date,
    group_by: str,
    segment_in: Optional[str],
    room_type_desc_in: Optional[str],
    local_region_in: Optional[str],
    nationality_in: Optional[str],
) -> Dict[str, Any]:

    seg_list = parse_csv_list(segment_in)
    rt_list = parse_csv_list(room_type_desc_in)
    lr_list = parse_csv_list(local_region_in)
    nat_list = parse_csv_list(nationality_in)

    filters_sql = ""
    filters_sql += _build_in_filter("segment", seg_list)
    filters_sql += _build_in_filter("room_type_desc", rt_list)
    filters_sql += _build_in_filter("local_region", lr_list)
    filters_sql += _build_in_filter("nationality", nat_list)

    group_key_expr = _get_group_key_expr(group_by)
    has_breakdown = group_key_expr is not None

    if has_breakdown:
        sql = f"""
        WITH
            toDate(:d_start) AS d_start,
            toDate(:d_end)   AS d_end,
            dateDiff('day', d_start, d_end) AS period_days
        SELECT
            group_key,
            sum(room_rate_per_night)   AS revenue_sum,
            count()                    AS room_sold,
            avg(room_rate_per_night)   AS arr_simple,
            uniqExact(reservation_id)  AS bookings_count,
            period_days
        FROM
        (
            SELECT
                reservation_id,
                room_rate AS room_rate_per_night,
                segment,
                room_type_desc,
                local_region,
                nationality,
                age,
                stay_date,
                {group_key_expr} AS group_key
            FROM
            (
                SELECT
                    reservation_id,
                    room_rate,
                    segment,
                    room_type_desc,
                    local_region,
                    nationality,
                    age,
                    greatest(arrival_date, d_start) AS overlap_start,
                    least(depart_date,  d_end)      AS overlap_end
                FROM default.datamart_reservations final
                WHERE
                    arrival_date <= d_end
                    AND depart_date  >= d_start
                    {filters_sql}
            ) AS r
            ARRAY JOIN
                arrayMap(
                    x -> r.overlap_start + x,
                    range(dateDiff('day', r.overlap_start, r.overlap_end) + 1)
                ) AS stay_date
        ) AS expanded
        GROUP BY
            group_key
        WITH ROLLUP
        ORDER BY
            group_key ASC NULLS FIRST
        """
    else:
        sql = f"""
        WITH
            toDate(:d_start) AS d_start,
            toDate(:d_end)   AS d_end,
            dateDiff('day', d_start, d_end) AS period_days
        SELECT
            NULL                         AS group_key,
            sum(room_rate_per_night)     AS revenue_sum,
            count()                      AS room_sold,
            avg(room_rate_per_night)     AS arr_simple,
            uniqExact(reservation_id)    AS bookings_count,
            period_days
        FROM
        (
            SELECT
                reservation_id,
                room_rate AS room_rate_per_night,
                segment,
                room_type_desc,
                local_region,
                nationality,
                age,
                stay_date
            FROM
            (
                SELECT
                    reservation_id,
                    room_rate,
                    segment,
                    room_type_desc,
                    local_region,
                    nationality,
                    age,
                    greatest(arrival_date, d_start) AS overlap_start,
                    least(depart_date,  d_end)      AS overlap_end
                FROM default.datamart_reservations final
                WHERE
                    arrival_date <= d_end
                    AND depart_date  >= d_start
                    {filters_sql}
            ) AS r
            ARRAY JOIN
                arrayMap(
                    x -> r.overlap_start + x,
                    range(dateDiff('day', r.overlap_start, r.overlap_end) + 1)
                ) AS stay_date
        ) AS expanded
        """

    rows = list(db.execute(text(sql), {"d_start": start, "d_end": end}))

    if not rows:
        return {
            "period": {
                "start": str(start),
                "end": str(end),
                "nights": (end - start).days,
            },
            "totals": {
                "revenue_sum": 0.0,
                "room_sold": 0,
                "arr_simple": 0.0,
                "bookings_count": 0,
            },
            "breakdown": [],
        }

    period_days = int(rows[0].period_days)

    total_row = None
    breakdown_rows = []
    for r in rows:
        if r.group_key is None and total_row is None:
            total_row = r
        else:
            breakdown_rows.append(r)

    if total_row is None:
        total_row = rows[0]

    totals = {
        "revenue_sum": float(total_row.revenue_sum or 0),
        "room_sold": int(total_row.room_sold or 0),
        "arr_simple": float(total_row.arr_simple or 0),
        "bookings_count": int(total_row.bookings_count or 0),
    }

    breakdown = []
    for row in breakdown_rows:
        key = row.group_key
        if key is None:
            continue
        if isinstance(key, str) and key.strip() == "":
            continue

        breakdown.append(
            {
                "key": key,
                "revenue_sum": float(row.revenue_sum or 0),
                "room_sold": int(row.room_sold or 0),
                "arr_simple": float(row.arr_simple or 0),
                "bookings_count": int(row.bookings_count or 0),
            }
        )

    return {
        "period": {
            "start": str(start),
            "end": str(end),
            "nights": period_days,
        },
        "totals": totals,
        "breakdown": breakdown,
    }