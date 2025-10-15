from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import httpx, os


class ChatKitSessionRequest(BaseModel):
    device_id: str = Field(min_length=1, max_length=128)


router = APIRouter(prefix="/api/chatkit", tags=["chatkit"])

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHATKIT_WORKFLOW_ID = os.getenv("CHATKIT_WORKFLOW_ID")


@router.post("/session")
async def create_chatkit_session(request: ChatKitSessionRequest):
    if not OPENAI_API_KEY or not CHATKIT_WORKFLOW_ID:
        raise HTTPException(500, "OPENAI_API_KEY atau CHATKIT_WORKFLOW_ID belum diset.")

    url = "https://api.openai.com/v1/chatkit/sessions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "OpenAI-Beta": "chatkit_beta=v1",
    }
    body = {
        "workflow": {"id": CHATKIT_WORKFLOW_ID},
        "user": request.device_id,
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()

            return {
                "client_secret": data.get("client_secret"),
                "expires_at": data.get("expires_at"),
                "session_id": data.get("id") or data.get("session_id"),
            }

    except httpx.HTTPStatusError as e:
        detail = (
            e.response.json()
            if e.response.headers.get("content-type", "").startswith("application/json")
            else {"error": {"message": e.response.text}}
        )
        raise HTTPException(
            e.response.status_code,
            f"Error dari OpenAI: {detail.get('error',{}).get('message','Unknown error')}",
        )
    except Exception as e:
        raise HTTPException(500, f"Terjadi kesalahan internal: {e}")
