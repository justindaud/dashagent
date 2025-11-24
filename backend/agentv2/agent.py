import asyncio
import os
import json
from dotenv import load_dotenv
load_dotenv()

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown

from agents import Agent, Runner, TResponseInputItem, ItemHelpers, trace
from openai.types.responses import ResponseTextDeltaEvent

from agentv2.agents_team.orchestrator import orchestrator
from agentv2.agents_team.prompt_agent import prompt_agent
from agentv2.agents_team.experience_agent import experience_agent

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from agents.extensions.memory.sqlalchemy_session import SQLAlchemySession

from agentv2.scripts.experience_func import fetch_experience, ingest_insights, ingest_insights_async

console = Console()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL.split(":", 1)[0]:
    # rewrite 'postgresql://' -> 'postgresql+asyncpg://'
    DATABASE_URL = "postgresql+asyncpg://" + DATABASE_URL[len("postgresql://"):]
elif DATABASE_URL.startswith("mysql://") and "+" not in DATABASE_URL.split(":", 1)[0]:
    # rewrite 'mysql://' -> 'mysql+aiomysql://'
    DATABASE_URL = "mysql+aiomysql://" + DATABASE_URL[len("mysql://"):]
elif DATABASE_URL.startswith("sqlite://") and "+" not in DATABASE_URL.split(":", 1)[0]:
    # rewrite 'sqlite:///' -> 'sqlite+aiosqlite:///'
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

def make_sa_session(session_id: str) -> SQLAlchemySession:
    # create_tables=True is convenient for dev; in production use migrations
    return SQLAlchemySession(
        session_id=session_id,
        engine=engine,
        create_tables=False,
    )

# Stream events
async def stream_once(result, session_id: str, user_id: str):
    """Jalankan satu turn dengan streaming events (session-managed)."""

    console.print(Panel.fit("[bold]=== Run Starting ===[/bold]", border_style="cyan"))

    # Tampilkan delta token + event penting (tool calls & outputs)
    assistant_buffer = []  # untuk merakit teks assistant dari delta
    tool_events = []       # koleksi event tool untuk distilasi
    agent_updates_count = 0
    
    async for event in result.stream_events():
        et = event.type

        # 1) Agent updates - REDUCED: Only show first few, then suppress
        if et == "agent_updated_stream_event":
            agent_updates_count += 1
            if agent_updates_count <= 2:  # Only show first 2 agent updates
                console.print(f"[cyan]Agent updated →[/cyan] [bold]{event.new_agent.name if hasattr(event.new_agent, 'name') else 'Unknown'}[/bold]")
            continue

        # 2) Token deltas - OPTIMIZED: Batch processing instead of per-token
        if et == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            # Collect tokens but don't print each one (major TPM saver)
            assistant_buffer.append(event.data.delta)
            continue

        # 3) Item-level events - OPTIMIZED: Only essential tool events
        if et == "run_item_stream_event":
            it = event.item
            if it.type == "tool_call_item":
                # Tool calls - Simplified output
                tool_name = getattr(it, 'name', 'unknown_tool')
                console.print(f"\n[yellow]→ Tool: {tool_name}[/yellow]")
                
                # Minimal tool input display
                if getattr(it, "input", None):
                    input_str = str(it.input)
                    if len(input_str) > 100: input_str = input_str[:100] + "…"
                    console.print(f"  Input: {input_str}")
                
                tool_events.append({
                    "type": "tool_call_start",
                    "name": tool_name,
                    "input_preview": str(getattr(it, 'input', ''))[:1000],  # Reduced from 5000
                })
                
            elif it.type == "tool_call_output_item":
                # Tool outputs - Simplified
                tool_name = getattr(it, 'name', 'unknown_tool')
                out = getattr(it, "output", "")
                
                # Truncate long outputs
                output_str = str(out)
                if len(output_str) > 200: output_str = output_str[:200] + "…"
                console.print(f"  Output: {output_str}")
                
                tool_events.append({
                    "type": "tool_call_output",
                    "name": tool_name,
                    "output_preview": output_str,
                })
                
            elif it.type == "message_output_item":
                # Message chunks
                text = ItemHelpers.text_message_output(it) or ""
                assistant_buffer.append(text)

    console.print("\n[bold]=== Run Complete ===[/bold]\n")

    # Final output - Only show if significant content
    final_text = "".join(assistant_buffer).strip() or (result.final_output or "")
    if final_text:
        try:
            console.print(Markdown(final_text))
        except Exception:
            console.print(final_text)
    
    return {"final_text": final_text, "tool_events": tool_events}

# ---------- messages helpers ----------
async def fetch_agent_messages(engine, session_id: str, run_id: Optional[str] = None, *, after_id: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not limit or limit <= 0:
        limit = 50

    if run_id:
        sql = """
          SELECT id, session_id, run_id, message_data, created_at
          FROM agent_messages
          WHERE session_id = :sid AND run_id = :rid AND id > :after_id
          ORDER BY id ASC
          LIMIT :limit
        """
        params = {"sid": session_id, "rid": run_id, "after_id": after_id, "limit": limit}
    else:
        sql = """
          SELECT id, session_id, run_id, message_data, created_at
          FROM agent_messages
          WHERE session_id = :sid AND id > :after_id
          ORDER BY id ASC
          LIMIT :limit
        """
        params = {"sid": session_id, "after_id": after_id, "limit": limit}

    async with engine.begin() as conn:
        res = await conn.execute(text(sql), params)
        for r in res:
            m = r._mapping
            raw = m["message_data"]
            try:
                msg = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                msg = {"text": str(raw)}

            created_at = m.get("created_at")

            rows.append({
                "id": int(m["id"]),
                "session_id": m["session_id"],
                "run_id": m.get("run_id"),
                "message": msg,
                "created_at": created_at,
            })
    return rows

async def get_last_message_id(engine, session_id: str) -> int:
    async with engine.begin() as conn:
        res = await conn.execute(
            text("SELECT COALESCE(MAX(id), 0) AS last_id FROM agent_messages WHERE session_id = :sid"),
            {"sid": session_id},
        )
        row = res.first()
        return int(row._mapping["last_id"]) if row else 0

async def tag_messages_with_run_id(engine, session_id: str, run_id: str, after_id: int) -> int:
    async with engine.begin() as conn:
        res = await conn.execute(
            text("""
                UPDATE agent_messages
                   SET run_id = :rid
                 WHERE session_id = :sid
                   AND id > :after_id
                   AND (run_id IS NULL OR run_id = '')
            """),
            {"sid": session_id, "rid": run_id, "after_id": after_id},
        )
        return res.rowcount or 0

class DashboardAgent:
    def __init__(self, user_input: str, session_id: str, user_id: str, session=None):
        self.user_input = user_input
        self.session_id = session_id
        self.user_id = user_id
        # Gunakan session yang diberikan atau buat yang baru
        self.session = session or make_sa_session(session_id)

    # decomposing prompt into multiple prompts
    async def decompose_prompt(self):
        with console.status("[bold cyan]Analyzing prompt...[/bold cyan]") as status:
        
            result = Runner.run_streamed(prompt_agent, input=self.user_input, session=self.session)
            await stream_once(result, self.session_id, self.user_id)

            console.print(f"[debug] Result: {result}")
            console.print(f"[debug] Final output: {result.final_output}")
            
            if result.final_output:
                console.print(Panel(f"[bold cyan]Prompt Analysis[/bold cyan]"))
                #console.print(f"[yellow]Thoughts:[/yellow] {result.final_output}")
                console.print("\n[yellow]Generated Prompts:[/yellow]")
                for i, prompt in enumerate(result.final_output.queries, 1):
                    console.print(f"  {i}. {prompt}")
                
                return result.final_output
            else:
                console.print("[red]No prompt analysis found[/red]")
                return None

    # analyzing each decomposed prompt
    async def analyzer(self, prompt_response=None):
        with trace("Analyzing", metadata={"prompt": self.user_input, "session_id": self.session_id}):

            if prompt_response is None:
                prompt_response = await self.decompose_prompt()

            console.status("[bold cyan]Orchestrating...[/bold cyan]")

            # run all decomposed prompts parallelly with orchestrator

            async def run_analysis(prompt, index):
                result = Runner.run_streamed(orchestrator, prompt, session=self.session)
                console.print(f"\n[bold]Analysis {index+1}:[/bold]")
                await stream_once(result, self.session_id, self.user_id)
            
            tasks = [asyncio.create_task(run_analysis(prompt, i)) 
                 for i, prompt in enumerate(prompt_response.queries)]
            
            await asyncio.gather(*tasks)

    async def memory_updater(self):
        with trace("Updating memory", metadata={"session_id": self.session_id, "user_id": self.user_id}):
            with console.status("[bold cyan]Updating memory...[/bold cyan]") as status_msg:

                try:
                    q = f"""
                        WITH latest AS (
                            SELECT session_id
                            FROM agent_sessions
                            ORDER BY updated_at DESC
                            LIMIT 1
                            )
                        SELECT s.session_id, x.last_insight_at
                        FROM agent_sessions s
                        LEFT JOIN LATERAL (
                            SELECT MAX(si.created_at) AS last_insight_at
                            FROM session_insights si
                            WHERE si.session_id = s.session_id
                        ) x ON TRUE
                        WHERE s.session_id NOT IN (SELECT session_id FROM latest)
                            AND (x.last_insight_at IS NULL OR x.last_insight_at < s.updated_at)
                        ORDER BY s.updated_at ASC
                        LIMIT 1;
                        """
                    console.print("[bold cyan]Fetching experience...[/bold cyan]")

                    async with engine.connect() as conn:
                        result = await conn.execute(text(q))
                        row = result.fetchone()
                    
                    #experience = fetch_experience(limit=500)

                    if not row or row[1] is not None:
                        console.print("[yellow]No new sessions to analyze[/yellow]")
                        return

                    self.session_id = row[0]

                    sql_session = SQLAlchemySession(session_id=self.session_id, engine=engine)
                    result = Runner.run_streamed(
                        experience_agent,
                        "Anda akan membaca keseluruhan pecakapan, pahami konteks, buat insights sebagai list dari hal-hal yang perlu diingat, sebutkan table, fields, sql, cara membuat query, link, cara menentukan url, dsb",
                        session=sql_session
                    )
                    await stream_once(result, self.session_id, self.user_id)

                    console.print("[bold cyan]Updating memory...[/bold cyan]")
                    if result.final_output:
                        status_msg = await ingest_insights_async(
                            session_id=self.session_id,
                            user_id=self.user_id,
                            insights=getattr(result.final_output, "insights", []) or [],
                            patterns=getattr(result.final_output, "patterns", []) or [],
                            preferences=getattr(result.final_output, "preferences", []) or [],
                            async_engine=engine,
                        )
                        console.print(f"[green]{status_msg}[/green]")
                    else:
                        console.print("[yellow]No insights generated from experience agent[/yellow]")
                    
                    console.print("[bold cyan]Memory updated successfully[/bold cyan]")
                except Exception as e:
                    console.print(f"[red]Error updating memory:[/red] {e}")

    async def run_and_collect(session_id: str, user_id: str, user_input: str, user_role: Optional[str] = None, run_id: Optional[str] = None) -> Dict[str, Any]:
        run_id = run_id or uuid.uuid4().hex

        start_marker_id = await get_last_message_id(engine, session_id)

        console.print(f"[bold]accepted[/bold] session_id={session_id} user_id={user_id} role={user_role} prompt={user_input!r} run={run_id}")

        sa_session = make_sa_session(session_id)
        agent = DashboardAgent(user_input=user_input, session_id=session_id, user_id=user_id, session=sa_session)

        ok, err = True, None
        try:
            analyzer_task = asyncio.create_task(agent.analyzer())
            memory_task  = asyncio.create_task(agent.memory_updater())
            await asyncio.gather(analyzer_task, memory_task)
        except Exception as e:
            ok, err = False, str(e)
            console.print(f"[red]runner.error[/red] session_id={session_id} user_id={user_id} role={user_role} run={run_id} error={e}")

        await tag_messages_with_run_id(engine, session_id, run_id, after_id=start_marker_id)

        messages = await fetch_agent_messages(engine, session_id, run_id=run_id, limit=500)

        return {
            "message": "Agent finished",
            "session_id": session_id,
            "user_id": user_id,
            "role": user_role,
            "run_id": run_id,
            "messages": messages,
        }
