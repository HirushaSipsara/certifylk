"""PostgreSQL-only regression coverage for the historical Alembic sequence.

Set ``TEST_POSTGRES_URL`` to a disposable PostgreSQL database when running this
test locally or in the migration CI job. The normal unit suite intentionally
does not invent a database server.
"""

import os
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from alembic import command

POSTGRES_URL = os.getenv("TEST_POSTGRES_URL")


@pytest.mark.skipif(
    not POSTGRES_URL, reason="TEST_POSTGRES_URL must point to a disposable PostgreSQL DB"
)
def test_postgres_historical_migration_sequence_and_seed() -> None:
    assert POSTGRES_URL is not None
    engine = create_engine(POSTGRES_URL)
    backend_dir = Path(__file__).resolve().parents[1]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", POSTGRES_URL)
    config.set_main_option("script_location", str(backend_dir / "alembic"))

    command.downgrade(config, "base")
    inspector = inspect(engine)
    assert "scheme_cost_items" not in inspector.get_table_names()

    command.upgrade(config, "20260805_0001")
    assert "scheme_cost_items" not in inspect(engine).get_table_names()

    command.upgrade(config, "20260807_0002")
    columns = {column["name"] for column in inspect(engine).get_columns("scheme_cost_items")}
    assert "scheme_cost_items" in inspect(engine).get_table_names()
    assert "is_quote_required" not in columns

    command.upgrade(config, "20260807_0003")
    with engine.connect() as connection:
        assert (
            connection.execute(
                text("SELECT count(*) FROM scheme_cost_items WHERE scheme_id = 'SLS_MARK_CORDIAL'")
            ).scalar_one()
            > 0
        )

    command.upgrade(config, "20260807_0004")
    command.upgrade(config, "20260807_0005")
    columns = {column["name"] for column in inspect(engine).get_columns("scheme_cost_items")}
    assert "is_quote_required" in columns
    assert (
        next(
            column
            for column in inspect(engine).get_columns("scheme_cost_items")
            if column["name"] == "is_quote_required"
        )["nullable"]
        is False
    )

    with engine.connect() as connection:
        assert (
            connection.execute(
                text(
                    "SELECT count(*) FROM scheme_cost_items "
                    "WHERE scheme_id = 'SLS_MARK_CORDIAL' AND is_quote_required = FALSE"
                )
            ).scalar_one()
            > 0
        )

    command.upgrade(config, "head")
    command.upgrade(config, "head")
