from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Assessment,
    AssessmentAnswer,
    AssessmentQuestion,
    CertificationScheme,
    ProcessStep,
    QuestionBank,
)
from app.models.enums import AssessmentStatus, QuestionPage
from app.services.assessment_service import create_assessment
from app.services.evidence_service import mark_evidence_unavailable
from app.services.process_service import build_evidence_plan
from app.services.result_service import generate_result
from app.services.seed_service import PROD_CORDIAL, seed_initial_knowledge_base


async def build_sample_assessment(db: Session) -> Assessment:
    """Build a synthetic read-only Fresh Fruit Cordial (SLS Mark) sample assessment."""
    if not db.scalar(
        select(CertificationScheme).where(CertificationScheme.id == "SLS_MARK_CORDIAL")
    ):
        seed_initial_knowledge_base(db)

    assessment = create_assessment(db, is_sample=True)
    assessment.scheme_id = "SLS_MARK_CORDIAL"
    assessment.profile_data = {
        "name": "Lanka Fresh Fruit Beverages Ltd",
        "business_type": "Formal Enterprise",
        "years_operating": 3,
        "scale": "Small (1-10 employees)",
        "market": ["Domestic Supermarkets", "Local Retail"],
        "existing_certifications": [],
        "has_food_licence": "yes",
        "monthly_volume_range": "1,000 - 5,000 L",
        "product_slug": "fresh-fruit-cordial",
        "product_id": str(PROD_CORDIAL),
        "product_name": "Fresh Fruit Cordial",
        "applicability_decision": {
            "recommended_path_scheme_id": "SLS_MARK_CORDIAL",
            "overall_reasoning": "Product quality certification under SLS 187 is recommended for fresh fruit cordial sold in domestic supermarkets.",
            "decisions": [
                {
                    "scheme_id": "SLS_MARK_CORDIAL",
                    "tier": "market_required",
                    "confidence": 0.95,
                    "reasoning": "SLS Mark under SLS 187 is widely required by domestic supermarket chains for fruit cordial products.",
                    "source_reference": "SLS 187 Specification for Fruit Cordials",
                    "scheme_name": "SLS Mark — Fresh Fruit Cordial",
                    "body_name": "Sri Lanka Standards Institution (SLSI)",
                    "typical_timeline_days": 365,
                    "summary": "Official quality mark certification for Fresh Fruit Cordial under SLS 187.",
                }
            ],
        },
    }

    # Populate 5 process steps
    steps = [
        "Receiving raw fresh fruit, sugar, and food-grade additives.",
        "Washing, peeling, inspection, and fruit juice extraction.",
        "Cooking, brix formulation adjustment, and pasteurization.",
        "Hot filling into pre-washed, sterilized glass bottles.",
        "Labeling, batch numbering, crate storage, and local distribution.",
    ]
    for idx, text in enumerate(steps, start=1):
        db.add(ProcessStep(assessment_id=assessment.id, position=idx, text=text))
    assessment.process_analysis = {
        "stages": [
            {"stage": "receiving", "description": steps[0]},
            {"stage": "preparation", "description": steps[1]},
            {"stage": "cooking", "description": steps[2]},
            {"stage": "filling", "description": steps[3]},
            {"stage": "storage", "description": steps[4]},
        ],
        "uncertainties": ["Cooking endpoint evidence is incomplete."],
    }
    for key, value in {
        "HYG_HAND_01": "always",
        "HYG_CLEAN_01": "recorded_each_batch",
        "HYG_CHEM_01": "locked_separate",
        "PACK_FILL_01": "dedicated_clean_area",
        "STORE_FIN_01": "separate_protected",
        "TRACE_CODE_01": "every_batch",
    }.items():
        db.add(
            AssessmentAnswer(
                assessment_id=assessment.id,
                page="clarification",
                key=key,
                value=value,
                created_at=assessment.created_at,
            )
        )

    # Build evidence plan from scheme evidence expectations
    assessment.status = AssessmentStatus.PROCESS_COMPLETE
    requests = build_evidence_plan(db, assessment)

    # Mark some evidence requests as unavailable to create realistic demonstration gaps/unknowns
    if len(requests) >= 2:
        mark_evidence_unavailable(db, assessment, requests[-1])

    assessment.status = AssessmentStatus.READY_TO_SCORE
    clarification_question = db.scalar(select(QuestionBank).where(QuestionBank.active.is_(True)))
    if clarification_question is not None:
        db.add(
            AssessmentQuestion(
                assessment_id=assessment.id,
                question_id=clarification_question.id,
                page=QuestionPage.CLARIFICATION,
                display_order=1,
                answered=True,
                created_at=assessment.created_at,
            )
        )
    db.flush()

    # Run deterministic scheme evaluation and score calculation
    await generate_result(db, assessment)
    db.commit()
    return assessment
