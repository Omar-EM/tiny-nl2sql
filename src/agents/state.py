from typing import Annotated
from pydantic import BaseModel
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class State(BaseModel):
    """State for the NL2SQL Agent"""

    messages: Annotated[list[BaseMessage], add_messages]
    user_query: str
    generated_sql: str | None = None
    is_safe: bool | None = None
    sql_execution_status: str = "Initialized"   # TODO: Should be an Enum
    sql_execution_result: str | None = None


def get_initial_state(messages: list[BaseMessage], query: str) -> State:
    return State(
        messages=messages,
        user_query=query,
    )