import os
import tempfile

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.models import SchemeCostItem
from app.services.seed_service import seed_initial_knowledge_base


def test_clean_database_migration_and_seed_regression():
    """Verify that a fresh clean database can migrate from base to head and seed data without NotNullViolation."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)

        # Configure Alembic to run against the fresh database
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_ini = os.path.join(backend_dir, "alembic.ini")
        alembic_cfg = Config(alembic_ini)
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))

        # Run migration upgrade head from base
        command.upgrade(alembic_cfg, "head")

        # Run demo seed on the migrated database
        with Session(engine) as session:
            seed_initial_knowledge_base(session)

            # Assert scheme_cost_items exist and is_quote_required is populated
            items = session.query(SchemeCostItem).all()
            assert len(items) > 0
            for item in items:
                assert item.is_quote_required is not None
                assert isinstance(item.is_quote_required, bool)

            # Assert explicitly quote-required items
            quote_req_count = session.scalar(
                select(func.count(SchemeCostItem.id)).where(SchemeCostItem.is_quote_required.is_(True))
            )
            priced_count = session.scalar(
                select(func.count(SchemeCostItem.id)).where(SchemeCostItem.is_quote_required.is_(False))
            )
            assert priced_count > 0
            assert quote_req_count is not None

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)

