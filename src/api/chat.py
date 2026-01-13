from fastapi import APIRouter
from .models import ChatRequest, ChatResponse


chat_router = APIRouter(prefix="/chat")


@chat_router.post('/')
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat endpoint that processes user messages through the NL2SQL agent."""

    # Generate session ID

    # Create user message

    # configure graph execution

    # Create initial graph state and start conversation

    # return result
    return {
        "message": "dummy msg",
        "session_id": "session_123",
        "metadata": None,
    }