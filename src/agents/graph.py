from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .nodes import (
    check_sql_validity_node,
    execute_sql_node,
    generate_sql_node,
    hitl_node,
    render_message_node,
    validate_sql_node,
)
from .nodes_enum import Node
from .state import State


def build_graph(checkpointer: BaseCheckpointSaver | None = None) -> StateGraph:
    graph = StateGraph(State)

    graph.add_node(Node.GENERATE_SQL.value, generate_sql_node)
    graph.add_node(Node.VALID_SQL.value, validate_sql_node)
    graph.add_node(Node.HITL.value, hitl_node)
    graph.add_node(Node.EXECUTE_SQL.value, execute_sql_node)
    graph.add_node(Node.RENDER_FINAL_MESSAGE.value, render_message_node)

    graph.add_edge(START, Node.GENERATE_SQL.value)
    graph.add_edge(Node.GENERATE_SQL.value, Node.VALID_SQL.value)

    graph.add_conditional_edges(
        Node.VALID_SQL.value,
        check_sql_validity_node,
        {"valid": Node.HITL.value, "invalid": END},
    )

    graph.add_edge(Node.EXECUTE_SQL.value, Node.RENDER_FINAL_MESSAGE.value)
    graph.add_edge(Node.RENDER_FINAL_MESSAGE.value, END)

    if checkpointer is None:
        checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)
