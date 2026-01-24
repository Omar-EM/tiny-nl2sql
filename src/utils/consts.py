import os
from pathlib import Path

UNSAFE_SQL_KW = ["DROP", "DELETE", "TRUNCATE", "ALTER", "UDPATE", "INSERT", "CREATE", "GRANT", "RENAME", "REVOKE", "DENY"]

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_SCHEMA_DIR = PROJECT_ROOT / "knowledge"
TABLES_FILE = PROJECT_ROOT / "dataset" / "tables.yaml"

DB_CONNECTION_STRING = f'postgresql://{os.getenv("PGUSER")}:{os.getenv("PGPASSWORD")}@{os.getenv("PGHOST")}:{int(os.getenv("PGPORT"))}/{os.getenv("PGDATABASE")}'
