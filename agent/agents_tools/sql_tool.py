from __future__ import annotations
import os, re
from dataclasses import dataclass
from typing import Any, Dict, List
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from agents import function_tool


FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|ATTACH|DETACH|VACUUM|PRAGMA)\b",
    re.I,
)

SELECT_RE = re.compile(r"^\s*SELECT\b", re.I)

def _sanitize_sql(sql: str) -> str:
    if FORBIDDEN.search(sql):
        raise ValueError("Only SELECT queries are allowed (no DDL/DML/PRAGMA/ATTACH).")
    if not SELECT_RE.match(sql):
        raise ValueError("Query must start with SELECT.")
    return sql.rstrip().rstrip(";")


@dataclass
class QueryResult:
    columns: List[str]
    rows: List[List[Any]]
    row_count: int


@function_tool()
def query_database(sql: str) -> Dict[str, Any]:
    """Jalankan SQL read‑only ke SQLite. Return rows ringkas."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")

    sanitized = _sanitize_sql(sql)

    engine = create_engine(
        db_url,
        future=True,
        pool_pre_ping=True,
    )
    with engine.connect() as conn: # type: Connection
        # PostgreSQL doesn't support PRAGMA, but we can ensure read-only
        # The FORBIDDEN regex already prevents DML/DDL operations
        pass

        cur = conn.execute(text(sanitized))
        cols = list(cur.keys())
        rows = [list(r) for r in cur.fetchall()]
        
        # Convert to structured format expected by QueryResult
        data = [dict(zip(cols, row)) for row in rows]
        
    return {
        "data": data,
        "schema": cols,
        "row_count": len(rows),
        "query_executed": sql,
        "metadata": {}
    }