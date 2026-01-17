from uuid import uuid4

from fastapi import APIRouter
from langchain_core.messages import HumanMessage

from ..agents.graph import build_graph
from ..agents.state import get_initial_state
from .models import ChatRequest, ChatResponse

chat_router = APIRouter(prefix="/chat")


@chat_router.post('/')
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat endpoint that processes user messages through the NL2SQL agent."""

    # Generate session ID
    session_id = request.session_id or str(uuid4())
    # Create user message
    user_query = HumanMessage(content=request.message)
    # configure graph execution
    config = {"configurable": {"thread_id": session_id}}
    # Create initial graph state and start conversation
    graph = build_graph()
    initial_state = get_initial_state(messages=[user_query], query=user_query.content)

    print("Start graph agent execution...")
    res = graph.invoke(initial_state, config=config)

    print(f"got {res=}")

    return {
        "message": "dummy msg",
        "session_id": "session_123",
        "metadata": None,
    }