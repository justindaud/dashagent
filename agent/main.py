import asyncio
from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown

from agents import Agent, Runner, TResponseInputItem, ItemHelpers, trace
from openai.types.responses import ResponseTextDeltaEvent

from agents_team.orchestrator import orchestrator
from session_manager import run_with_session, generate_session_id

console = Console()

async def stream_once(convo: list[TResponseInputItem]) -> list[TResponseInputItem]:
    """Jalankan satu turn dengan streaming events.
       Return: input list berikutnya (updated with tool outputs & assistant response)."""

    # Mulai run_streamed
    result = Runner.run_streamed(orchestrator, convo)

    console.print(Panel.fit("[bold]=== Run Starting ===[/bold]", border_style="cyan"))

    # Tampilkan delta token + event penting (tool calls & outputs)
    assistant_buffer = []  # untuk merakit teks assistant dari delta
    async for event in result.stream_events():
        et = event.type

        # 1) Perubahan agent (jarang, tapi ditampilkan untuk debug)
        if et == "agent_updated_stream_event":
            console.print(f"[cyan]Agent updated →[/cyan] [bold]{event.new_agent}[/bold]")
            continue

        # 2) Event token delta mentah (opsional)
        if et == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            # jika mau efek "mengetik", bisa print delta di sini:
            console.print(event.data.delta, end="", soft_wrap=True)
            assistant_buffer.append(event.data.delta)
            continue

        # 3) Item-level events (alat & pesan)
        if et == "run_item_stream_event":
            it = event.item
            if it.type == "tool_call_item":
                # tool dipanggil
                console.print(f"\n[yellow]→ Tool called:[/yellow] [bold]{it}[/bold]")
                if getattr(it, "input", None):
                    # ringkasan input tool (jangan terlalu panjang)
                    s = str(it.input)
                    if len(s) > 300: s = s[:300] + "…"
                    console.print(Panel(s, title="tool input", border_style="yellow"))
            elif it.type == "tool_call_output_item":
                # hasil tool
                out = getattr(it, "output", "")
                # ringkas kalau panjang
                s = str(out)
                if len(s) > 800: s = s[:800] + "…"
                console.print(Panel(s, title=f"tool output: {getattr(it,'name','')}", border_style="green"))
            elif it.type == "message_output_item":
                # sebagian SDK mengirim message chunks di sini
                text = ItemHelpers.text_message_output(it) or ""
                assistant_buffer.append(text)

    console.print("\n[bold]=== Run Complete ===[/bold]\n")

    # Rakitan jawaban akhir (fallback: result.final_output)
    final_text = "".join(assistant_buffer).strip() or (result.final_output or "")
    if final_text:
        try:
            # render markdown jika perlu
            console.print(Markdown(final_text))
        except Exception:
            console.print(final_text)

    # Perbarui convo untuk turn berikutnya
    return result.to_input_list()

async def main():
    console.print("[bold cyan]DashAgent - Hotel Analytics AI (Auto Session)[/bold cyan]")
    console.print("Ketik 'exit' untuk keluar.")
    
    # Auto session generation
    user_id = Prompt.ask("Enter user ID", default="demo_user")
    session_id = generate_session_id(user_id)
    console.print(f"[green]Session created:[/green] {session_id}")
    
    convo: list[TResponseInputItem] = []
    while True:
        user_input = console.input("\n[bold]You:[/bold] ").strip()
        if not user_input:
            console.print("[red]Pertanyaan kosong.[/red]"); continue
        if user_input.lower() in {"exit", "quit", ":q"}:
            console.print("Bye! 👋"); break

        convo.append({"content": user_input, "role": "user"})

        # Bungkus setiap turn dengan trace bawaan SDK (akan muncul di log SDK)
        with trace("orchestrator_turn", metadata={"question": user_input, "session_id": session_id}):
            try:
                # Option 1: Use session management
                if user_input.startswith("/session"):
                    # Use session management for specific queries
                    result = await run_with_session(
                        orchestrator,
                        user_input,
                        session_id,
                        user_id
                    )
                    console.print(f"[green]Session Result:[/green] {result}")
                else:
                    # Use regular streaming
                    convo = await stream_once(convo)
                    
            except Exception as e:
                console.print(f"[red]Error getting response:[/red] {e}")

if __name__ == "__main__":
    asyncio.run(main())