from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Chat request model"""

    message: str
    session_id: str | None = None

class RequestStatus(BaseModel):
    """status of the request"""

    session_id: str
    is_awaiting_approval: bool


class ChatResponse(BaseModel):
    """Chat response model"""

    session_id: str
    message: str
    metadata: dict[str, Any] | None = None
