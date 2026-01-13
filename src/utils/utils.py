import yaml
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate


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
    target_prompt: str, file_path: str | Path="prompts/prompts.yaml"
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
        raise ValueError(f"Prompt template {target_prompt} not found in the prompt file at {file_path}")

    return ChatPromptTemplate.from_messages(
        ("system", prompts[target_prompt]["system_prompt"]),
        ("user", prompts[target_prompt]["user_prompt"]),
    )