from typing import Annotated
from pydantic import BaseModel
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class State(BaseModel):
    """State for the NL2SQL Agent"""

    messages: Annotated[list[BaseMessage], add_messages]
    user_query: str | None = None
    generated_sql: str | None = None
    is_safe: bool
    sql_execution_status: str
    sql_execution_result: str
