from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Chat request model"""

    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    """Chat response model"""

    message: str
    session_id: str
    metadata: dict[str, Any] | None = None
