import re
from typing import Literal

import psycopg2
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import JsonOutputParser
from langgraph.types import interrupt, Command
from langgraph.graph import END

from ..services.schema_loader import init_data_dictionary
from .enums import Node, AgentStatus
from ..utils.consts import DB_CONNECTION_STRING, UNSAFE_SQL_KW
from ..utils.utils import _validate_sql_syntax, load_chat_prompt_template
from .state import State

data_dict = init_data_dictionary()


def generate_sql_node(state: State) -> dict:
    """Generates SQL query from natural language using LLM"""
    print("[NODE] SQL Generator")

    # Get history context
    chat_history = "\n".join(
        f"{msg.type.upper()}: {msg.content}" for msg in state["messages"]
    )
    # Get prompt
    sql_generator_prompt = load_chat_prompt_template(target_prompt="sql_generator")

    # Call LLM
    llm = init_chat_model(
        "gemini-2.5-flash",
        model_provider="google_genai",
        temperature=0,
        model_kwargs={"response_mime_type": "application/json"},
        # model_kwargs={"response_format": "json_response"}
    )  # .with_structured_output(method="json_mode")

    chain = sql_generator_prompt | llm | JsonOutputParser()
    response = chain.invoke(
        {
            "user_query": state["user_query"],
            "chat_history": chat_history,
            "schema_context": data_dict.format_context(),
            # "sql_example": "" # To add later on (few-shot prompting)
        }
    )

    return {**response, "status": AgentStatus.PENDING}


def validate_sql_node(state: State) -> dict:
    """Validate if the SQL"""

    print("[NODE] sql_validator ...", state)
    unsafe_kw_found = []
    for kw in UNSAFE_SQL_KW:
        if re.search(rf"\b{kw}\b", state["generated_sql"].upper()):
            unsafe_kw_found.append(kw)

    if unsafe_kw_found:
        print(f"SQL contains unsafe keywords ... {unsafe_kw_found}")
        ai_message = AIMessage(content="Agent run interrupted. Query unsafe !")
        return {"messages": [ai_message], "is_safe": False}
    else:
        try:
            is_valid_syntax = _validate_sql_syntax(state["generated_sql"])
        except Exception:
            is_valid_syntax = False

        return {"is_safe": True, "is_valid_syntax": is_valid_syntax}


def hitl_node(state: State) -> Command:
    """Get the human approval"""

    interrupt_message = format_interrupt_message({
        "generated_sql": state["generated_sql"],
        "sql_explanation": state["sql_explanation"]
    })

    human_feedback = interrupt(interrupt_message)

    return Command(goto=Node.EXECUTE_SQL.value if human_feedback.lower()=='y' else END)


def execute_sql_node(state: State) -> dict:
    """Excute the generated sql query"""
    print("[NODE] execute SQL query")
    try:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
    except Exception as e:
        print(f"Cannot connect to db: {e}")

    with conn.cursor() as cur:
        try:
            cur.execute(state["generated_sql"])
            res = cur.fetchall()
        except (Exception, psycopg2.DatabaseError) as e:
            print(e)

    return {"sql_execution_result": str(res)}


def render_message_node(state: State) -> dict:
    """Get the LLM to render the final message (the result of the query, else the resulting error)"""
    print("[NODE] render message")

    # Call LLM
    llm = init_chat_model(
        "gemini-2.5-flash",
        model_provider="google_genai",
        temperature=0,
        # model_kwargs={"response_mime_type": "application/json"},
        # model_kwargs={"response_format": "json_response"}
    )  # .with_structured_output(method="json_mode")

    # Get prompt
    sql_generator_prompt = load_chat_prompt_template(target_prompt="result_analyzer")

    ai_final_response = (sql_generator_prompt | llm).invoke(
        {
            "user_query": state["user_query"],
            "sql_query": str(state["generated_sql"]),
            "query_results": str(state["sql_execution_result"]),
        }
    )

    return {"ai_message": ai_final_response, "status": AgentStatus.DONE}


#################################
# Routing Nodes
#################################


def check_sql_validity_node(state: State) -> Literal["valid", "invalid"]:
    print("[ROUTING NODE] checking sql query validity")
    return "valid" if state["is_safe"] else "invalid"


# Helper functions

def format_interrupt_message(dict_to_format: dict):
    formatted = "Generated SQL: " + dict_to_format["generated_sql"]

    formatted += '\nExplanation: ' + dict_to_format["sql_explanation"]

    return formatted
    