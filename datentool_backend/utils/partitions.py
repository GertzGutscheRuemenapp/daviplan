from django.db import models, connection
from psqlextra.backend.schema import PostgresSchemaEditor


def add_partition(model: models.Model, name: str, values):
    """Add Table Partition to model if not exists"""
    schema_editor: PostgresSchemaEditor = connection.schema_editor()

    partition_tablename = schema_editor.quote_name(
        schema_editor.create_partition_table_name(
        model=model,
        name=name,
    ))

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"SELECT to_regclass('{partition_tablename}')")
        partition_exists = cursor.fetchone()[0]

    if not partition_exists:
        schema_editor.add_list_partition(
            model=model,
            name=name,
            values=[values],
        )

def truncate_partition_table(model: models.Model, name: str):
    """Truncate partitioned table"""
    schema_editor: PostgresSchemaEditor = connection.schema_editor()

    partition_tablename = schema_editor.quote_name(
        schema_editor.create_partition_table_name(
        model=model,
        name=name,
    ))
    sql = f'DELETE FROM {partition_tablename}'
    schema_editor.execute(sql)


def delete_partition_table(model: models.Model, name: str):
    """Delete partitioned table"""
    schema_editor: PostgresSchemaEditor = connection.schema_editor()
    schema_editor.delete_partition(model, name)

