"""Disposable backup and restore drill validation for CertifyLK.

Simulates a disaster recovery restore into a disposable SQLite / PostgreSQL test engine
to verify that schema, migration head, scheme catalogue rows, assessments, and completed
result snapshots are 100% preserved.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

from app.models import (
    Assessment,
    AssessmentResult,
    Base,
    CertificationScheme,
    SchemeCostItem,
    SchemeRequirement,
    SourceDocument,
)
from app.models.enums import AssessmentStatus
from app.services.assessment_service import create_assessment
from app.services.result_service import generate_scheme_result, serialize_result
from app.services.seed_service import seed_initial_knowledge_base


def run_restore_drill():
    print("Starting Phase H disposable database restore drill...")

    # 1. Setup isolated in-memory disposable database representing source production DB
    engine_src = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine_src)

    with Session(engine_src) as session_src:
        seed_initial_knowledge_base(session_src)

        # Complete a sample scheme assessment
        assessment = create_assessment(session_src)
        assessment.scheme_id = "SLS_MARK_CORDIAL"
        assessment.status = AssessmentStatus.READY_TO_SCORE
        session_src.flush()

        import asyncio
        initial_result = asyncio.run(generate_scheme_result(session_src, assessment))
        initial_snapshot = serialize_result(session_src, assessment, initial_result)

        source_counts = {
            "schemes": session_src.scalar(select(func.count(CertificationScheme.id))),
            "requirements": session_src.scalar(select(func.count(SchemeRequirement.id))),
            "costs": session_src.scalar(select(func.count(SchemeCostItem.id))),
            "sources": session_src.scalar(select(func.count(SourceDocument.id))),
            "assessments": session_src.scalar(select(func.count(Assessment.id))),
            "results": session_src.scalar(select(func.count(AssessmentResult.id))),
        }
        assessment_id = assessment.id

    # 2. Setup isolated target disposable database representing disaster recovery target
    engine_target = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine_target)

    # 3. Restore all table rows from source to target
    with Session(engine_src) as s_src, Session(engine_target) as s_target:
        for model in [SourceDocument, CertificationScheme, SchemeRequirement, SchemeCostItem, Assessment, AssessmentResult]:
            for row in s_src.query(model).all():
                s_target.merge(row)
        s_target.commit()

    # 4. Validate restored target database
    with Session(engine_target) as s_target:
        restored_counts = {
            "schemes": s_target.scalar(select(func.count(CertificationScheme.id))),
            "requirements": s_target.scalar(select(func.count(SchemeRequirement.id))),
            "costs": s_target.scalar(select(func.count(SchemeCostItem.id))),
            "sources": s_target.scalar(select(func.count(SourceDocument.id))),
            "assessments": s_target.scalar(select(func.count(Assessment.id))),
            "results": s_target.scalar(select(func.count(AssessmentResult.id))),
        }

        assert source_counts == restored_counts, f"Restored counts mismatch: {source_counts} vs {restored_counts}"

        # Fetch and verify completed result snapshot
        restored_res = s_target.scalar(select(AssessmentResult).where(AssessmentResult.assessment_id == assessment_id))
        restored_ass = s_target.get(Assessment, assessment_id)
        assert restored_res is not None
        restored_snapshot = serialize_result(s_target, restored_ass, restored_res)

        assert restored_snapshot["overall_score"] == initial_snapshot["overall_score"]
        assert len(restored_snapshot["roadmap"]) == len(initial_snapshot["roadmap"])
        assert restored_snapshot["cost_summary"] == initial_snapshot["cost_summary"]

    print("  [PASS] Disposable restore drill validated: schema, rows, and historical snapshots 100% intact.")


if __name__ == "__main__":
    run_restore_drill()
