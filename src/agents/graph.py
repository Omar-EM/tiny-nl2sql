from langgraph.graph import START, END, StateGraph
from .state import State
from .nodes import sql_executor, sql_generator, sql_validator, check_sql_validity
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver


def build_graph(checkpointer: BaseCheckpointSaver | None = None) -> StateGraph:
    graph = StateGraph(State)

    graph.add_node("generate_sql", sql_generator)
    graph.add_node("validate_sql", sql_validator)
    graph.add_node("execute_sql", sql_executor)
    # graph.add_node("validity_check", check_sql_validity)

    graph.add_edge(START, "generate_sql")
    graph.add_edge("generate_sql", "validate_sql")

    graph.add_conditional_edges("validate_sql", check_sql_validity, {"valid": "execute_sql", "invalide": END})
    graph.add_edge("execute_sql", END)

    if checkpointer is None:
        checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)
