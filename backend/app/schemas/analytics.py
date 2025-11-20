# app/schemas/analytics.py
from typing import List
from app.utils.trim import TrimmedModel


class DimensionsResponse(TrimmedModel):
    segment: List[str] = []
    nationality: List[str] = []
    local_region: List[str] = []
    room_type_desc: List[str] = []


class AggregatePeriod(TrimmedModel):
    start: str
    end: str
    nights: int


class AggregateTotals(TrimmedModel):
    revenue_sum: float
    room_sold: int
    arr_simple: float
    bookings_count: int
    room_sold_per_room: float
    room_count: int


class AggregateBreakdownItem(TrimmedModel):
    key: str
    revenue_sum: float
    room_sold: int
    arr_simple: float
    bookings_count: int
    room_sold_per_room: float


class AggregateResponse(TrimmedModel):
    period: AggregatePeriod
    totals: AggregateTotals
    breakdown: List[AggregateBreakdownItem] = []
