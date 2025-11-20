# app/schemas/dashboard.py
from app.utils.trim import TrimmedModel
from datetime import datetime

class DashboardStats(TrimmedModel):
    total_guests: int
    total_reservations: int
    total_chats: int
    total_transactions: int
    latest_depart_date: str | None
    last_updated: str | None

class RecentUpload(TrimmedModel):
    id: int
    filename: str
    file_type: str
    status: str
    rows_processed: int | None
    created_at: datetime