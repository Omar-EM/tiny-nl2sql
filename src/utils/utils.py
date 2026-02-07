from pathlib import Path

import yaml
from langchain_core.prompts import ChatPromptTemplate
from sqlglot import ParseError, exp, parse_one


class UnsafeQueryException(Exception):
    pass


def load_config(config_path: str | Path) -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path) as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file not found at: {config_path}")
        raise
    except yaml.YAMLError as e:
        print("Error while parsing the yaml config file:", str(e))
        raise


def load_chat_prompt_template(
    target_prompt: str, file_path: str | Path = "prompts/prompts.yaml"
) -> ChatPromptTemplate:
    """Set up a prompt template from a YAML file.

    Args:
        file_path: Path to the prompt YAML file
        target_prompt: Name of the prompt to load from YAML file

    Returns:
        Langchain's ChatPromptTemplate
    """

    prompts = load_config(file_path)
    if prompts.get(target_prompt) is None:
        raise ValueError(
            f"Prompt template {target_prompt} not found in the prompt file at {file_path}"
        )

    return ChatPromptTemplate.from_messages(
        [
            ("system", prompts[target_prompt]["system_prompt"]),
            ("human", prompts[target_prompt]["user_prompt"]),
        ]
    )


def _validate_sql_syntax(query: str) -> bool:
    try:
        parsed_query = parse_one(query, read="postgres")

        # Only allow 'SELECT' statements:   (redundant safety validation)
        if not isinstance(parsed_query, exp.Select):
            raise UnsafeQueryException(
                f"Expected a 'SELECT' query, got {type(parsed_query).__name__}"
            )  # TODO: Create custom exception
        return True

    except Exception as e:
        error_messages = {
            ParseError: f"SQL parsing error: {str(e)}",
            UnsafeQueryException: f"Unsafe query {str(e)}",
        }
        print(error_messages.get(type(e), f"Unknown exception {str(e)}"))

        raise
