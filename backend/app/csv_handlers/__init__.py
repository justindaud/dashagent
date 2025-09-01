"""
CSV Handlers Registry

This module provides a registry pattern for CSV handlers,
making it easy to add new CSV types without modifying existing code.
"""
from typing import Dict, Optional, Protocol
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import UploadFile


class CSVHandler(Protocol):
    """Protocol for CSV handlers"""
    
    async def process_csv(self, file: UploadFile, db: Session) -> dict:
        """Process uploaded CSV file"""
        ...


# Import all handlers first
from .profile_tamu import ProfileTamuHandler
from .reservasi import ReservasiHandler
from .chat_whatsapp import ChatWhatsappHandler
from .transaksi_resto import TransaksiRestoHandler

# Registry of CSV handlers
CSV_HANDLERS = {
    "profile_tamu": ProfileTamuHandler(),
    "reservasi": ReservasiHandler(),
    "chat_whatsapp": ChatWhatsappHandler(),
    "transaksi_resto": TransaksiRestoHandler()
}

def get_csv_handler(file_type: str):
    """Get CSV handler for specific file type"""
    if file_type not in CSV_HANDLERS:
        raise ValueError(f"Unsupported file type: {file_type}")
    return CSV_HANDLERS[file_type]
