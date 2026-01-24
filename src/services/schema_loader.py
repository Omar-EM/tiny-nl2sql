import yaml
from pathlib import Path
from typing import Annotated, Any
from dotenv import load_dotenv
load_dotenv(override=True)

from pydantic import BaseModel, BeforeValidator, Field
from sqlalchemy.engine.reflection import Inspector
import sqlalchemy as sa

from ..utils.consts import OUTPUT_SCHEMA_DIR, TABLES_FILE, DB_CONNECTION_STRING
from ..utils.utils import load_config


class ColumnInfo(BaseModel):
    name: str
    type_: Annotated[str, Field(alias="type"), BeforeValidator(lambda t: str(t))]
    nullable: bool
    comment: str | None
    is_primary_key: bool


class TableInfo(BaseModel):
    """Class that contains informations about a table"""

    name: str
    schema_name: str
    columns: list[ColumnInfo]
    primary_keys: list[str]
    foreign_keys: list[dict[str, Any]]
    description: str | None

    @classmethod
    def from_inspector(
        cls, inspector: Inspector, table_name: str, schema_name: str
    ) -> "TableInfo":
        """Use's SQLAlchemy's Inspector to reflect the table"""

        columns = inspector.get_columns(table_name, schema_name)
        primary_keys = inspector.get_pk_constraint(table_name, schema_name)[
            "constrained_columns"
        ]
        foreign_keys = inspector.get_foreign_keys(table_name, schema_name)
        description = inspector.get_table_comment(table_name, schema_name).get("text")
        columns_info = [
            ColumnInfo(**c, is_primary_key=(c["name"] in primary_keys)) for c in columns
        ]

        return cls(
            name=table_name,
            schema_name=schema_name,
            columns=columns_info,
            primary_keys=primary_keys,
            foreign_keys=foreign_keys,
            description=description,
        )


class SchemaInfo(BaseModel):
    """Class that represents a schema in the db"""

    name: str
    tables: dict[str, TableInfo]

    @classmethod
    def from_inspector(
        cls, inspector: Inspector, schema_name: str
    ) -> "SchemaInfo":
        return cls(
            name=schema_name,
            tables={
                table_name: TableInfo.from_inspector(inspector, table_name, schema_name)
                for table_name in inspector.get_table_names(schema_name)
            }
        )


class DatabaseInfo(BaseModel):
    """Class that represents a database in the postgres"""

    name: str
    schemas: dict[str, SchemaInfo]


class DataDictionary(BaseModel):
    """Main data dictionary that contains all the databases information"""

    databases: dict[str, DatabaseInfo]

    @classmethod
    def from_inspector(
        cls, inspector: Inspector, database_schema_dict: dict,
    ) -> "DatabaseInfo":
        databases = {}
        for db_name, schemas in database_schema_dict.items():
            schemas_models = {}
            for schema_name in schemas:
                schemas_models[schema_name] = SchemaInfo.from_inspector(inspector, schema_name)
            databases[db_name] = DatabaseInfo(name=db_name, schemas=schemas_models)

        return cls(databases=databases)

    def save(self, output_path: Path | str) -> Path | str:
        if isinstance(output_path, str):
            output_path = Path(output_path)

        OUTPUT_SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
        if not output_path:
            output_path = OUTPUT_SCHEMA_DIR / "knowledge_dict.yaml"
        
        with output_path.open("w") as file:
            yaml.dump(self.model_dump(), file, sort_keys=False)

        return output_path
        

if __name__ == "__main__":
    engine = sa.create_engine(DB_CONNECTION_STRING)
    inspector = sa.inspect(engine)

    db_schemas_dict = load_config(TABLES_FILE)

    data_dictionary = DataDictionary.from_inspector(inspector, db_schemas_dict)
    data_dictionary.save(None)
