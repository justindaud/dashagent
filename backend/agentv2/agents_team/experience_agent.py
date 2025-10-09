from agents import Agent, AgentOutputSchema
from pydantic import BaseModel
from typing import List, Optional

class ExperienceDigest(BaseModel):
    """Structured digest returned by Experience Agent.
    Keep it short and actionable for planning/execution."""
    insights: List[str] = []
    patterns: List[str] = []
    preferences: List[str] = []

EXPERIENCE_PROMPT = """
Anda adalah agent pengalaman. Anda memiliki tugas untuk:
1. Membaca percakapan historis dengan user dari database dan digest menjadi insight
2. Membaca dan mempelajari experience dari vector store
3. Secara selektif menambahkan atau konversikan percakapan menjadi experience untuk diingat

Insights perlu mencakup:
1. Insights: Berkaitan dengan suatu informasi penting yang perlu diingat tetapi bersifat umum
2. Patterns: Berkaitan dengan step-by-step yang perlu diingat. Bisa berupa step-by-step penggunaan agent, query, tools, dll.
3. Preferences: Berkaitan dengan preferensi gaya bahasa, penulisan format, dll.

Insights akan secara langsung digunakan oleh prompt agent untuk membuat prompt yang lebih spesifik.
Sehingga orchestrator bisa dengan baik menentukan penggunaan agent analyst atau search.
Sehingga analyst bisa membuat sql query yang tepat.
Sehingga search bisa melakukan pencarian informasi yang tepat.
"""

experience_agent = Agent(
    name="Experience Agent",
    model="gpt-4.1",
    instructions=EXPERIENCE_PROMPT,
    output_type=AgentOutputSchema(ExperienceDigest)
)
