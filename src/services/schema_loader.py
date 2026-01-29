from pathlib import Path
from typing import Annotated, Any

import yaml
from dotenv import load_dotenv

load_dotenv(override=True)

import sqlalchemy as sa
from pydantic import BaseModel, BeforeValidator, Field
from sqlalchemy.engine.reflection import Inspector

from ..utils.consts import DB_CONNECTION_STRING, OUTPUT_SCHEMA_DIR, TABLES_FILE
from ..utils.utils import load_config


class ColumnInfo(BaseModel):
    name: str
    type_: Annotated[str, Field(alias="type"), BeforeValidator(lambda t: str(t))]
    nullable: bool
    comment: str | None
    is_primary_key: bool

    def __str__(self):
        s = f"{self.name} ({self.type_.upper()}), NULLABLE ({self.nullable}), "
        if self.comment:
            s += "DESCRIPTION ({self.comment})"

        return s


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

    def format_context(self) -> str:
        context = f"\t\t<TABLE ({self.name}) COLUMNS:>\n".expandtabs(4)
        for c in self.columns:
            context += f"\t\t\t-  {c!s} \n".expandtabs(4)

        context += f"\t\t</TABLE ({self.name}) COLUMNS:>\n".expandtabs(4)
        return context


class SchemaInfo(BaseModel):
    """Class that represents a schema in the db"""

    name: str
    tables: dict[str, TableInfo]

    @classmethod
    def from_inspector(cls, inspector: Inspector, schema_name: str) -> "SchemaInfo":
        return cls(
            name=schema_name,
            tables={
                table_name: TableInfo.from_inspector(inspector, table_name, schema_name)
                for table_name in inspector.get_table_names(schema_name)
            },
        )

    def format_context(self) -> str:
        context = f"\t<SCHEMA: {self.name}>\n".expandtabs(4)
        for table in self.tables.values():
            context += table.format_context() + "\n"
        context += f"\t</SCHEMA: {self.name}>".expandtabs(4)

        return context


class DatabaseInfo(BaseModel):
    """Class that represents a database in the postgres"""

    name: str
    schemas: dict[str, SchemaInfo]

    def format_context(self) -> str:
        context = f"<DATABASE: {self.name}>\n"
        for schema in self.schemas.values():
            context += schema.format_context() + "\n"
        context += f"</DATABASE: {self.name}>\n\n"

        return context


class DataDictionary(BaseModel):
    """Main data dictionary that contains all the databases information"""

    databases: dict[str, DatabaseInfo]

    @classmethod
    def from_inspector(
        cls,
        inspector: Inspector,
        database_schema_dict: dict,
    ) -> "DatabaseInfo":
        databases = {}
        for db_name, schemas in database_schema_dict.items():
            schemas_models = {}
            for schema_name in schemas:
                schemas_models[schema_name] = SchemaInfo.from_inspector(
                    inspector, schema_name
                )
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

    def format_context(self) -> str:
        #context = "DATABASES:\n"
        context = ""
        for database in self.databases.values():
            context += database.format_context()

        return context


def init_data_dictionary():
    engine = sa.create_engine(DB_CONNECTION_STRING)
    inspector = sa.inspect(engine)

    db_schemas_dict = load_config(TABLES_FILE)

    return DataDictionary.from_inspector(inspector, db_schemas_dict)
    # print(data_dictionary.format_context())
    # data_dictionary.save(None)
