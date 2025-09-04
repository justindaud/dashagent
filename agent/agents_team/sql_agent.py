from agents import Agent
from agents_tools.sql_tool import query_database
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from agents import AgentOutputSchema


class QueryResult(BaseModel):
    """Structured output for SQL Agent queries"""
    data: List[Dict[str, Any]]
    schema: List[str]
    row_count: int
    query_executed: str
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None


sql_agent = Agent(
    name="SQL",
    model="gpt-4o-mini",
    instructions=(
        "Anda memiliki peranan untuk menulis query SQL menyesuaikan spesifikasi.\n"
        "Hasil query tersebut akan anda eksekusi untuk mendapatkan data dari database.\n"
        "Berkaitan dengan sekuritas, agent ini tidak bisa INSERT, UPDATE, DELETE, dan DROP.\n"
        "Pastikan tersusun untuk SQL read‑only.\n\n"
        "PENTING: Untuk analisis yang sophisticated, kembalikan RAW DATA bukan aggregated data.\n"
        "- Gunakan SELECT dengan kolom individual (reservation_id, arrival_date, room_rate, dll)\n"
        "- Hindari aggregation functions (SUM, AVG, COUNT) kecuali diminta spesifik\n"
        "- Berikan data yang cukup untuk Analyst Agent melakukan advanced analysis\n"
        "- Gunakan WHERE clause untuk filtering yang tepat\n"
        "- Limit hasil jika terlalu besar (max 10000 rows untuk performance)\n\n"
        "Return structured output dengan data, schema, row_count, dan metadata."
    ),
    tools=[query_database],
    output_type=AgentOutputSchema(QueryResult, strict_json_schema=False)
)