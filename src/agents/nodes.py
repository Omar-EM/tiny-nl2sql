import re
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage

from ..services.schema_loader import init_data_dictionary
from ..utils.consts import UNSAFE_SQL_KW
from ..utils.utils import _validate_sql_syntax, load_chat_prompt_template
from .state import State

data_dict = init_data_dictionary()

def generate_sql_node(state: State) -> dict:
    """Generates SQL query from natiral language using LLM"""
    print("[NODE] SQL Generator")

    # Get history context
    chat_history = "\n".join(
        f"{msg.type.upper()}: {msg.content}" for msg in state.messages
    )
    # Get schema context
    schema_context = data_dict.format_context()
    # Get prompt
    sql_generator_prompt = load_chat_prompt_template(target_prompt="sql_generator")

    # Call LLM
    llm = init_chat_model(
        "gemini-2.5-flash", model_provider="google_genai", temperature=0
    )  # .with_structured_output(method="json_mode")

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


def validate_sql_node(state: State) -> dict:
    """Validate if the SQL"""

    print("[NODE] sql_validator ...")
    unsafe_kw_found = []
    for kw in UNSAFE_SQL_KW:
        if re.search(rf"\b{kw}\b", state.generated_sql.upper()):
            unsafe_kw_found.append(kw)

    if unsafe_kw_found:
        print(f"SQL contains unsafe keywords ... {unsafe_kw_found}")
        ai_message = AIMessage(content="Agent run interrupted. Query unsafe !")
        return {"messages": [ai_message], "is_safe": False}
    else:
        try:
            is_valid_syntax = _validate_sql_syntax(state.generated_sql)
        except Exception:
            is_valid_syntax = False

        return {"is_safe": True, "is_valid_syntax": is_valid_syntax}


def execute_sql_node(state: State) -> dict:
    print("[NODE] execute SQL query")

    return {"sql_execution_status": "true", "sql_execution_result": "sql result"}


#################################
# Routing Nodes
#################################


def check_sql_validity_node(state: State) -> Literal["valid", "invalid"]:
    print("[ROUTING NODE] checking sql query validity")
    return "valid" if state.is_safe else "invalide"
