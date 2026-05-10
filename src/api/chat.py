import asyncio
from uuid import uuid4

import mlflow
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from ..agents.enums import AgentStatus
from ..agents.graph import get_graph
from ..agents.state import get_initial_state
from .schemas import (
    ChatRequest,
    GetStatusResponse,
    PostStatusResponse,
    ResumeRequest,
    SessionResult,
)

chat_router = APIRouter(prefix="/chat")

_session_queues: dict[str, asyncio.Queue] = {}


@mlflow.trace(name="nl2sql-graph-execution")
async def run_full_session(graph: CompiledStateGraph, user_query: str, session_id: str):
    initial_state = get_initial_state(messages=[], query=user_query)
    config = {"configurable": {"thread_id": session_id}}

    print("Start graph agent execution...")
    await graph.ainvoke(initial_state, config=config)

    queue: asyncio.Queue = asyncio.Queue()
    _session_queues[session_id] = queue
    feedback = await queue.get()
    _session_queues.pop(session_id, None)

    print(f"Resuming session {session_id} with feedback: {feedback}")
    await graph.ainvoke(Command(resume=feedback), config=config)


@chat_router.post("/", response_model=PostStatusResponse)
async def create_session(
    request: ChatRequest,
    background_task: BackgroundTasks,
    graph: CompiledStateGraph = Depends(get_graph),
):
    """Chat endpoint that processes user messages through the NL2SQL agent."""
    session_id = request.session_id or str(uuid4())
    background_task.add_task(run_full_session, graph, request.message, session_id)
    return {"session_id": session_id, "status": AgentStatus.INITIALIZED}


@chat_router.get("/{session_id}/status", response_model=GetStatusResponse)
async def get_session_status(
    session_id: str, graph: CompiledStateGraph = Depends(get_graph)
):
    config = {"configurable": {"thread_id": session_id}}
    graph_state = graph.get_state(config)
    if not graph_state.values:
        raise HTTPException(404, detail=f"session with id: ({session_id}) not found")

    is_awaiting_approval = len(graph_state.interrupts) > 0
    status = (
        AgentStatus.WAITING_APPROVAL
        if is_awaiting_approval
        else graph_state.values.get("status", AgentStatus.INITIALIZED)
    )

    return {
        "session_id": session_id,
        "status": status,
        "is_awaiting_approval": is_awaiting_approval,
    }


@chat_router.get("/{session_id}/approval")
async def get_pending_approval(
    session_id: str, graph: CompiledStateGraph = Depends(get_graph)
):
    config = {"configurable": {"thread_id": session_id}}
    graph_state = graph.get_state(config)

    if not graph_state.interrupts:
        raise HTTPException(404, detail="No pending approvals for this session")

    return {
        "session_id": session_id,
        "status": graph_state.values.get("status", AgentStatus.INITIALIZED),
        "is_awaiting_approval": True,
        "interrupt_data": graph_state.interrupts[0].value,
    }


@chat_router.post("/{session_id}/approval", response_model=PostStatusResponse)
async def approve_execution(
    request: ResumeRequest,
    session_id: str,
):
    queue = _session_queues.get(session_id)
    if queue is None:
        raise HTTPException(404, detail=f"No pending approval for session {session_id}")
    await queue.put(request.feedback)
    return {"session_id": session_id, "status": AgentStatus.RUNNING}


@chat_router.get("/{session_id}/results", response_model=SessionResult)
async def get_session_results(session_id: str, graph=Depends(get_graph)):
    graph_state = graph.get_state({"configurable": {"thread_id": session_id}})

    if not graph_state.values:
        raise HTTPException(404, detail="Session result not found")

    return {
        "session_id": session_id,
        "status": AgentStatus.DONE,
        "model_response": graph_state.values["ai_message"].content,
    }
