"""PostgreSQL-only regression coverage for the historical Alembic sequence.

Set ``TEST_POSTGRES_URL`` to a disposable PostgreSQL database when running this
test locally or in the migration CI job. The normal unit suite intentionally
does not invent a database server.
"""

import os
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from alembic import command
from app.core.config import get_settings
from app.db.session import get_db
from app.main import app
from app.services.seed_service import seed_initial_knowledge_base

POSTGRES_URL = os.getenv("TEST_POSTGRES_URL")


@pytest.mark.skipif(
    not POSTGRES_URL, reason="TEST_POSTGRES_URL must point to a disposable PostgreSQL DB"
)
def test_postgres_historical_migration_sequence_and_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    assert POSTGRES_URL is not None
    monkeypatch.setenv("DATABASE_URL", POSTGRES_URL)
    get_settings.cache_clear()
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
    command.upgrade(config, "20260807_0006")
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

    observation_columns = {
        column["name"] for column in inspect(engine).get_columns("evidence_observations")
    }
    assert {"scheme_id", "scheme_requirement_id"}.issubset(observation_columns)

    # Reproduce the legacy production constraint that prevented scheme IDs from
    # being stored in requirement_id, then verify revision 0007 removes it.
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE evidence_observations "
                "ADD CONSTRAINT fk_evidence_observations_requirement_id_requirements "
                "FOREIGN KEY (requirement_id) REFERENCES requirements(id)"
            )
        )
    command.upgrade(config, "20260807_0007")
    assert not any(
        foreign_key["constrained_columns"] == ["requirement_id"]
        and foreign_key["referred_table"] == "requirements"
        for foreign_key in inspect(engine).get_foreign_keys("evidence_observations")
    )
    command.upgrade(config, "20260809_0008")
    observation_columns = {
        column["name"]: column for column in inspect(engine).get_columns("evidence_observations")
    }
    assert observation_columns["fallback_used"]["nullable"] is False
    assert observation_columns["validation_status"]["nullable"] is False

    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_factory() as session:
        seed_initial_knowledge_base(session)

    def override_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            sample = client.post("/api/v1/assessments/sample")
            assert sample.status_code == 201, sample.text
            sample_body = sample.json()
            assert sample_body["status"] == "completed"
            result = client.get(f"/api/v1/assessments/{sample_body['id']}/result")
            assert result.status_code == 200, result.text
            assert result.json()["overall_score"] == 32
    finally:
        app.dependency_overrides.clear()

    command.upgrade(config, "head")
    command.upgrade(config, "head")

    with engine.connect() as connection:
        assert (
            connection.execute(
                text("SELECT kind FROM evidence_expectations WHERE id = 'EV_SLS_HYG_HANDWASH'")
            ).scalar_one()
            == "photo"
        )
        assert (
            connection.execute(
                text(
                    "SELECT evaluation_rule ->> 'question' FROM scheme_requirements "
                    "WHERE id = 'SLS_HYG_HANDWASH'"
                )
            ).scalar_one()
            == "HYG_HAND_01"
        )

    critical_columns = {
        "assessments": {"scheme_id", "scheme_version", "catalogue_revision"},
        "assessment_results": {
            "roadmap_snapshot",
            "scheme_id",
            "scheme_version",
            "catalogue_revision",
        },
        "requirement_evaluations": {"scheme_id", "scheme_requirement_id"},
        "scheme_cost_items": {"is_quote_required"},
        "evidence_observations": {
            "scheme_id",
            "scheme_requirement_id",
            "fallback_used",
            "validation_status",
        },
    }
    for table, required in critical_columns.items():
        actual = {column["name"] for column in inspect(engine).get_columns(table)}
        assert required.issubset(actual), f"Missing columns in {table}: {required - actual}"
