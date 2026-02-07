from enum import Enum


class Node(str, Enum):
    GENERATE_SQL = "generate_sql"
    VALID_SQL = "valid_sql"
    HITL = "interrupt_HITL"
    EXECUTE_SQL = "execute_sql"
    RENDER_FINAL_MESSAGE = "render_message"


class AgentStatus(str, Enum):
    INITIALIZED = "initialized"
    PENDING = "pending"
    WAITING_APPROVAL = "waiting approval"
    DONE = "done"
    FAILED = "failed"
