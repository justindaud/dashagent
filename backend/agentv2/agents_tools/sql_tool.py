from agents import function_tool
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

CLICKHOUSE_URL_AGENT = os.getenv("CLICKHOUSE_URL_AGENT")


@function_tool
def query_database(query: str) -> str:
    """
    Execute SQL query on the hotel ClickHouse database and return results.
    
    Args:
        query: SQL query string to execute
        
    Returns:
        Query results as formatted string
    """
    if not CLICKHOUSE_URL_AGENT:
        return "Error: CLICKHOUSE_URL_AGENT is not set in environment variables."

    try:
        engine = create_engine(
            CLICKHOUSE_URL_AGENT,
            future=True,
            pool_pre_ping=True,
        )

        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = result.fetchall()

            if not rows:
                return "No data found for the given query."

            columns = result.keys()
            formatted_results = []

            # Header
            header = " | ".join(str(col) for col in columns)
            formatted_results.append(header)
            formatted_results.append("-" * len(header))

            # Rows
            for row in rows:
                row_str = " | ".join(str(val) for val in row)
                formatted_results.append(row_str)

            return "\n".join(formatted_results)

    except Exception as e:
        return f"Error executing ClickHouse query: {str(e)}"
