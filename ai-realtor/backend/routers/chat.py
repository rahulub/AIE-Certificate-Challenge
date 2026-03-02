import re
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent import run_agent
from checkpoint import get_history, save_messages, clear_thread

router = APIRouter()

# When user asks about these, don't pass inspection-heavy history — avoids echoing report summary
_NEIGHBORHOOD_KEYWORDS = re.compile(
    r"\b(neighborhood|schools?|area|walkability|safety|amenities|location|community|crime|parks?|nearby)\b",
    re.I,
)


def _is_neighborhood_question(message: str) -> bool:
    """True if the question is about neighborhood/schools/area (not inspection)."""
    return bool(_NEIGHBORHOOD_KEYWORDS.search(message.strip()))


class ChatRequest(BaseModel):
    message: str
    context: str = ""
    thread_id: str | None = None


class ClearRequest(BaseModel):
    thread_id: str


async def _stream_with_checkpoint(thread_id: str, message: str, context: str):
    """Streams agent response and checkpointes to Redis when done."""
    history = await get_history(thread_id) if thread_id else []
    if _is_neighborhood_question(message):
        history = []
    accumulated = []

    async for token in run_agent(message, context, history):
        accumulated.append(token)
        yield token

    if thread_id:
        await save_messages(
            thread_id,
            [
                {"role": "user", "content": message},
                {"role": "assistant", "content": "".join(accumulated)},
            ],
        )


@router.post("/chat")
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    thread_id = request.thread_id or str(uuid.uuid4())
    generated = request.thread_id is None

    response = StreamingResponse(
        _stream_with_checkpoint(thread_id, request.message, request.context),
        media_type="text/event-stream",
    )
    if generated:
        response.headers["X-Thread-Id"] = thread_id
    return response


@router.delete("/chat/thread/{thread_id}")
async def clear_chat_thread(thread_id: str):
    """Clear checkpointed history for this thread (called when user clicks Clear Chat)."""
    await clear_thread(thread_id)
    return {"status": "cleared"}
