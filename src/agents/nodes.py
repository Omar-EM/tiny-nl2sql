from typing import Literal
from .state import State
from ..utils.utils import load_chat_prompt_template
from random import random

from langchain.chat_models import init_chat_model


def sql_generator(state: State) -> dict:
    """Generates SQL query from natiral language using LLM"""
    print("[NODE] SQL Generator")

    # Get history context
    chat_history = "\n".join(
        f"{msg.type.upper()}: {msg.content}" for msg in state.messages
    )
    # Get schema context
    schema_context = "This is a dummy schema context"
    # Get prompt
    sql_generator_prompt = load_chat_prompt_template(target_prompt="sql_generator")

    # Call LLM
    llm = init_chat_model("google_genai:gemini-2.5-flash-lite").with_structured_output(
        method="json_mode"
    )

    chain = sql_generator_prompt | llm

    response = chain.invoke(
        {
            "user_query": state.user_query,
            "chat_history": chat_history,
            "schema_context": schema_context,
            # "sql_example": "" # To add later on (few-shot prompting)
        }
    )

    return response

def sql_validator(state: State) -> dict:
    """Validate if the SQL """

    # dummy logic
    if random.random() < 0.5:
        is_safe = True
    else:
        is_safe = False

    print("[NODE] sql_validator ...", is_safe)

    return {
        "is_safe": is_safe
    }

def sql_executor(state: State) -> dict:
    print("[NODE] execute SQL query")

    return {
        "sql_execution_status": "true",
        "sql_execution_result": "sql result"
    }


#################################
# Routing Nodes
#################################

def check_sql_validity(state: State) -> Literal["valid", "invalid"]:
    print("[ROUTING NODE] checking sql query validity")
    return "valid" if state.is_safe else "invlide"

