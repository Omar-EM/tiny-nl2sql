from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .nodes import (
    check_sql_validity_node,
    execute_sql_node,
    generate_sql_node,
    render_message_node,
    validate_sql_node,
    hitl_node
)
from .state import State


def build_graph(checkpointer: BaseCheckpointSaver | None = None) -> StateGraph:
    graph = StateGraph(State)

    graph.add_node("generate_sql", generate_sql_node)
    graph.add_node("validate_sql", validate_sql_node)
    graph.add_node("interrupt_HITL", hitl_node)
    graph.add_node("execute_sql", execute_sql_node)
    graph.add_node("render_message", render_message_node)

    graph.add_edge(START, "generate_sql")
    graph.add_edge("generate_sql", "validate_sql")

    graph.add_conditional_edges(
        "validate_sql",
        check_sql_validity_node,
        {"valid": "interrupt_HITL", "invalid": END},
    )

    graph.add_conditional_edges(
        "interrupt_HITL",
        hitl_node,
        {"approved": "execute_sql", "rejected": END}
    )
    graph.add_edge("execute_sql", "render_message")
    graph.add_edge("render_message", END)

    if checkpointer is None:
        checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)
