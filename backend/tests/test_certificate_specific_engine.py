from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Assessment,
    AssessmentQuestion,
    EvidenceObservation,
    EvidenceRequest,
    QuestionBank,
    RequirementEvaluation,
)
from app.models.enums import (
    AssessmentStatus,
    EvidenceKind,
    EvidenceRequestStatus,
    ObservationPolarity,
    QuestionPage,
)
from app.services.applicability_service import create_business_profile, run_applicability_agent
from app.services.catalog_service import (
    get_evidence_expectations,
    get_scheme,
    get_scheme_cost_items,
    get_scheme_requirements,
    get_source_documents,
)
from app.services.result_service import generate_scheme_result, serialize_result


def test_source_register_and_evidence_expectations_are_seeded(db: Session) -> None:
    sources = get_source_documents(db)
    assert {source.id for source in sources} >= {
        "SRC_SLS_187_CORDIAL_DRAFT",
        "SRC_SLS_GMP_DRAFT",
        "SRC_SLS_HACCP_DRAFT",
        "SRC_ISO_22000_2018_DRAFT",
    }
    assert all(source.content_verified is False for source in sources)

    requirements = get_scheme_requirements(db, "SLS_MARK_CORDIAL")
    expectations = get_evidence_expectations(db, "SLS_MARK_CORDIAL")
    assert len(expectations) == len(requirements)
    assert {item.requirement_id for item in expectations} == {item.id for item in requirements}
    assert {item.kind for item in expectations}.issubset(
        {"photo", "document", "lab_report", "licence", "declaration"}
    )


@pytest.mark.asyncio
async def test_applicability_freezes_scheme_version_and_revision(db: Session) -> None:
    profile = create_business_profile(
        db,
        name="Ceylon Cordials",
        business_type="limited_company",
        years_operating=3,
        scale="small",
        market=["supermarket"],
        existing_certifications=[],
        has_food_licence="yes",
        monthly_volume_range="500_2000",
        additional_info="Fresh fruit cordial for Sri Lankan supermarkets.",
    )
    assessment = Assessment(
        status=AssessmentStatus.DRAFT_PROFILE,
        business_profile_id=profile.id,
    )
    db.add(assessment)
    db.commit()

    decision = await run_applicability_agent(db, assessment)
    scheme = get_scheme(db, decision.recommended_path_scheme_id or "")
    assert scheme is not None
    assert assessment.scheme_id == scheme.id
    assert assessment.scheme_version == scheme.standard_version
    assert assessment.catalogue_revision == scheme.catalogue_revision


@pytest.mark.asyncio
async def test_scheme_completion_uses_scheme_requirements_and_cost_snapshot(
    db: Session,
) -> None:
    scheme = get_scheme(db, "SLS_GMP")
    assert scheme is not None
    requirements = get_scheme_requirements(db, scheme.id)
    costs = get_scheme_cost_items(db, scheme.id)
    supported_requirement = requirements[0]
    request = EvidenceRequest(
        assessment_id=None,  # type: ignore[arg-type]
        evidence_type="scheme_support",
        kind=EvidenceKind.PHOTO,
        title="Scheme-specific supporting evidence",
        requirement_ids=[supported_requirement.id],
        required=True,
        status=EvidenceRequestStatus.ANALYZED,
        display_order=1,
    )
    question = db.scalar(select(QuestionBank).limit(1))
    assert question is not None
    assessment = Assessment(
        status=AssessmentStatus.READY_TO_SCORE,
        scheme_id=scheme.id,
        scheme_version=scheme.standard_version,
        catalogue_revision=scheme.catalogue_revision,
    )
    db.add(assessment)
    db.flush()
    request.assessment_id = assessment.id
    db.add(request)
    db.flush()
    db.add(
        EvidenceObservation(
            assessment_id=assessment.id,
            evidence_request_id=request.id,
            requirement_id=supported_requirement.id,
            scheme_id=scheme.id,
            scheme_requirement_id=supported_requirement.id,
            polarity=ObservationPolarity.SUPPORTS,
            text="The supplied evidence supports this scheme requirement.",
            confidence=Decimal("0.9000"),
            provider="mock",
            created_at=datetime.now(timezone.utc),
        )
    )
    db.add(
        AssessmentQuestion(
            assessment_id=assessment.id,
            question_id=question.id,
            page=QuestionPage.CLARIFICATION,
            display_order=1,
            planning_rationale="test completion gate",
            answered=True,
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    result = await generate_scheme_result(db, assessment)
    serialized = serialize_result(db, assessment, result)

    assert result.scheme_id == scheme.id
    assert result.scheme_version == scheme.standard_version
    assert result.catalogue_revision == scheme.catalogue_revision
    assert result.scoring_version == "scheme-v1"
    assert result.roadmap_snapshot
    assert {item["recommendation_id"] for item in result.roadmap_snapshot}.issubset(
        {cost.id for cost in costs}
    )
    assert serialized["roadmap"]
    assert any(item["requirement_id"] == supported_requirement.id for item in result.strengths)

    evaluations = list(
        db.scalars(
            select(RequirementEvaluation).where(
                RequirementEvaluation.assessment_id == assessment.id
            )
        )
    )
    assert len(evaluations) == len(requirements)
    assert all(item.scheme_id == scheme.id for item in evaluations)
    assert all(
        item.scheme_requirement_id in {req.id for req in requirements} for item in evaluations
    )
