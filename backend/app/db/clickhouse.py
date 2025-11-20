# app/db/clickhouse.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from collections.abc import Generator

from app.config.settings import settings

clickhouse_engine = create_engine(
    settings.clickhouse_url,
    echo=False,
    pool_pre_ping=True,
)

ClickHouseSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=clickhouse_engine,
)

def get_clickhouse_db() -> Generator[Session, None, None]:
    db = ClickHouseSessionLocal()
    try:
        yield db
    finally:
        db.close()
