from decimal import Decimal
from typing import Any, cast

from sqlalchemy.orm import Session

from app.data.catalog import (
    CATALOGUE_REVIEW_DATE,
    QUESTION_BANK,
    RECOMMENDATIONS,
    REQUIREMENTS,
)
from app.models import CostItem, QuestionBank, Recommendation, Requirement
from app.models.enums import RequirementCategory


def seed_catalogue(db: Session) -> dict[str, int]:
    for item in REQUIREMENTS:
        db.merge(
            Requirement(
                id=str(item["id"]),
                category=RequirementCategory(str(item["category"])),
                title=str(item["title"]),
                description=str(item["description"]),
                weight=Decimal(str(item["weight"])),
                safety_critical=bool(item["safety_critical"]),
                applicability_tags=cast(list[str], item.get("applicability_tags", [])),
                evaluation_rule=cast(dict[str, Any], item["evaluation_rule"]),
                active=True,
            )
        )

    for item in QUESTION_BANK:
        db.merge(
            QuestionBank(
                id=str(item["id"]),
                category=str(item["category"]),
                text=str(item["text"]),
                options=cast(list[dict[str, str]], item["options"]),
                allows_other=bool(item["allows_other"]),
                product_tags=cast(list[str], item["product_tags"]),
                process_tags=cast(list[str], item["process_tags"]),
                requirement_ids=cast(list[str], item["requirement_ids"]),
                priority=cast(int, item["priority"]),
                page_eligibility=cast(list[str], item["page_eligibility"]),
                active=True,
            )
        )

    for (
        rec_id,
        title,
        steps,
        requirement_ids,
        priority,
        is_capex,
        one_min,
        one_max,
        recurring_min,
        recurring_max,
        note,
    ) in RECOMMENDATIONS:
        db.merge(
            Recommendation(
                id=rec_id,
                title=title,
                implementation_steps=steps,
                requirement_ids=requirement_ids,
                priority_base=priority,
                is_capex=is_capex,
                cost_note=note,
                last_reviewed=CATALOGUE_REVIEW_DATE,
                active=True,
            )
        )
        db.merge(
            CostItem(
                id=f"COST_{rec_id}",
                recommendation_id=rec_id,
                one_time_min=one_min,
                one_time_max=one_max,
                recurring_min=recurring_min,
                recurring_max=recurring_max,
                currency="LKR",
                effective_date=CATALOGUE_REVIEW_DATE,
                last_reviewed=CATALOGUE_REVIEW_DATE,
            )
        )

    db.commit()
    return {
        "requirements": len(REQUIREMENTS),
        "questions": len(QUESTION_BANK),
        "recommendations": len(RECOMMENDATIONS),
    }
