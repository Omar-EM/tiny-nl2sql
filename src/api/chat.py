from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from langchain_core.messages import HumanMessage

from ..agents.enums import AgentStatus
from ..agents.graph import get_graph
from ..agents.state import get_initial_state
from .schemas import ChatRequest, GetStatusResponse, InitialPostStatusResponse

chat_router = APIRouter(prefix="/chat")


async def run_agent(graph, user_query: str, session_id: str):
    initial_state = get_initial_state(
        messages=[], query=user_query.content
    )  # OEM: No msg history handled for now

    config = {"configurable": {"thread_id": session_id}}

    print("Start graph agent execution...")
    await graph.ainvoke(initial_state, config=config)


@chat_router.post("/", response_model=InitialPostStatusResponse)
async def create_session(
    request: ChatRequest,
    background_task: BackgroundTasks,
    graph=Depends(get_graph),
):
    """Chat endpoint that processes user messages through the NL2SQL agent."""

    session_id = request.session_id or str(uuid4())
    background_task.add_task(
        run_agent, graph, HumanMessage(content=request.message), session_id
    )

    return {
        "session_id": session_id,
        "status": AgentStatus.INITIALIZED,
    }


@chat_router.get("/{session_id}/status", response_model=GetStatusResponse)
async def get_session_status(session_id: str, graph=Depends(get_graph)):
    config = {"configurable": {"thread_id": session_id}}
    graph_state = graph.get_state(config)
    if not graph_state.values:  # TODO: (REMINDER) check for a better way
        raise HTTPException(404, detail=f"session with id: ({session_id}) not found")

    return {
        "session_id": session_id,
        "status": AgentStatus.INITIALIZED,
        "is_awaiting_approval": len(graph_state.interrupts) > 0,
    }


@chat_router.get("/{session_id}/approval")
async def get_pending_approval(session_id: str, graph=Depends(get_graph)):
    config = {"configurable": {"thread_id": session_id}}
    graph_state = graph.get_state(config)

    if not graph_state.interrupts:
        raise HTTPException(404, detail="No pending approvals for this session")

    return {
        "session_id": session_id,
        "status": AgentStatus.INITIALIZED,
        "is_awaiting_approval": len(graph_state.interrupts) > 0,
        "interrupt_data": graph_state.interrupts[0].value,
    }
