from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class State(TypedDict):
    """State for the NL2SQL Agent"""

    messages: Annotated[list[BaseMessage], add_messages]
    user_query: str
    
    # Generation node state
    generated_sql: str | None = None
    sql_explanation: str | None = None

    # Validation node state
    is_safe: bool | None = None
    is_valid_syntax: bool | None = None

    # HITL state
    human_feedback: str | None = None
    is_interrupted: bool = False

    # SQL execution node state
    sql_execution_status: str = "Initialized"  # TODO: Should be an Enum
    sql_execution_result: str | None = None
    ai_message: BaseMessage | None = None


def get_initial_state(messages: list[BaseMessage], query: str) -> State:
    return State(
        messages=messages,
        user_query=query,
    )
