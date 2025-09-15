from agents import function_tool
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

@function_tool
def query_database(query: str) -> str:
    """
    Execute SQL query on the hotel database and return results.
    
    Args:
        query: SQL query string to execute
        
    Returns:
        Query results as formatted string
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return "Error: DATABASE_URL not set"
    
    try:
        engine = create_engine(db_url, future=True, pool_pre_ping=True)
        
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = result.fetchall()
            
            if not rows:
                return "No data found for the given query."
            
            # Format results
            columns = result.keys()
            formatted_results = []
            
            # Add header
            header = " | ".join(str(col) for col in columns)
            formatted_results.append(header)
            formatted_results.append("-" * len(header))
            
            # Add rows
            for row in rows:
                row_str = " | ".join(str(val) for val in row)
                formatted_results.append(row_str)
            
            return "\n".join(formatted_results)
            
    except Exception as e:
        return f"Error executing query: {str(e)}"

# Export the function directly for use in agents
# query_database is already available as a function
