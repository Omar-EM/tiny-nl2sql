from pydantic import BaseModel
from ..agents.enums import AgentStatus


class ChatRequest(BaseModel):
    """Chat request model"""

    message: str
    session_id: str | None = None


class BaseStatusResponse(BaseModel):
    """Status when first instantiating the agentic workflow"""

    session_id: str
    status: AgentStatus


class InitialPostStatusResponse(BaseStatusResponse):
    """Status when first instantiating the agentic workflow"""
    pass


class GetStatusResponse(BaseStatusResponse):
    """Status once the agentic workflow kicks out"""

    is_awaiting_approval: bool


class ApprovalStatusResponse(GetStatusResponse):
    """response status when the interrupt data is requested"""

    interrupt_data: str | dict
