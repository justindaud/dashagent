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
    room_sold: int
    bookings_count: int
    room_count: int
    revenue_sum: float
    occupancy_rate: float
    average_occupancy_rate: float
    arr_simple: float
    adr_simple: float

class AggregateBreakdownItem(TrimmedModel):
    key: str
    room_sold: int
    bookings_count: int
    room_count: int
    revenue_sum: float
    occupancy_rate: float
    average_occupancy_rate: float
    arr_simple: float
    adr_simple: float


class AggregateResponse(TrimmedModel):
    period: AggregatePeriod
    totals: AggregateTotals
    breakdown: List[AggregateBreakdownItem] = []
