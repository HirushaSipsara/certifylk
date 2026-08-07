import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Assessment,
    AssessmentResult,
    Category,
    CertificationBody,
    CertificationScheme,
    EvidenceExpectation,
    QuestionBank,
    SchemeCostItem,
    SchemeRequirement,
    SourceDocument,
)
from app.models.enums import AssessmentStatus
from app.services.assessment_service import create_assessment
from app.services.result_service import generate_scheme_result, serialize_result
from app.services.seed_service import seed_initial_knowledge_base


@pytest.mark.asyncio
async def test_historical_snapshot_immutability(db_session: Session):
    """Verify completed assessment result snapshot remains immutable even after seed data changes."""
    seed_initial_knowledge_base(db_session)

    assessment = create_assessment(db_session)
    assessment.scheme_id = "SLS_MARK_CORDIAL"
    assessment.status = AssessmentStatus.READY_TO_SCORE
    db_session.flush()

    initial_result = await generate_scheme_result(db_session, assessment)
    initial_serialized = serialize_result(db_session, assessment, initial_result)

    recorded_score = initial_serialized["overall_score"]
    recorded_roadmap_len = len(initial_serialized["roadmap"])

    # Re-run seed_initial_knowledge_base
    seed_initial_knowledge_base(db_session)
    db_session.flush()

    # Re-fetch assessment result
    res_after = db_session.scalar(
        select(AssessmentResult).where(AssessmentResult.assessment_id == assessment.id)
    )
    assert res_after is not None
    serialized_after = serialize_result(db_session, assessment, res_after)

    assert serialized_after["overall_score"] == recorded_score
    assert len(serialized_after["roadmap"]) == recorded_roadmap_len
    assert serialized_after["cost_summary"] == initial_serialized["cost_summary"]


@pytest.mark.asyncio
async def test_catalogue_seed_idempotency_row_counts(db_session: Session):
    """Verify running seed_initial_knowledge_base twice produces exact identical row counts and zero duplicates."""
    # First seed
    seed_initial_knowledge_base(db_session)
    counts_1 = {
        "schemes": db_session.scalar(select(func.count(CertificationScheme.id))),
        "sources": db_session.scalar(select(func.count(SourceDocument.id))),
        "requirements": db_session.scalar(select(func.count(SchemeRequirement.id))),
        "expectations": db_session.scalar(select(func.count(EvidenceExpectation.id))),
        "costs": db_session.scalar(select(func.count(SchemeCostItem.id))),
        "categories": db_session.scalar(select(func.count(Category.id))),
        "bodies": db_session.scalar(select(func.count(CertificationBody.id))),
    }

    # Second seed
    seed_initial_knowledge_base(db_session)
    counts_2 = {
        "schemes": db_session.scalar(select(func.count(CertificationScheme.id))),
        "sources": db_session.scalar(select(func.count(SourceDocument.id))),
        "requirements": db_session.scalar(select(func.count(SchemeRequirement.id))),
        "expectations": db_session.scalar(select(func.count(EvidenceExpectation.id))),
        "costs": db_session.scalar(select(func.count(SchemeCostItem.id))),
        "categories": db_session.scalar(select(func.count(Category.id))),
        "bodies": db_session.scalar(select(func.count(CertificationBody.id))),
    }

    assert counts_1 == counts_2
    assert counts_1["schemes"] > 0
    assert counts_1["requirements"] > 0
    assert counts_1["costs"] > 0
