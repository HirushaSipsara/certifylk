from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.models import Requirement
from app.models.enums import RequirementStatus

MULTIPLIERS = {
    RequirementStatus.CONFIRMED: Decimal("1.0"),
    RequirementStatus.PARTIAL: Decimal("0.5"),
    RequirementStatus.GAP: Decimal("0.0"),
    RequirementStatus.UNKNOWN: Decimal("0.0"),
    RequirementStatus.NOT_APPLICABLE: Decimal("0.0"),
}


@dataclass(frozen=True)
class EvaluatedRequirement:
    requirement_id: str
    category: str
    title: str
    weight: Decimal
    safety_critical: bool
    status: RequirementStatus
    multiplier: Decimal
    evidence_references: list[str]
    rationale: str


def load_applicable_requirements(
    requirements: list[Requirement], product_tags: set[str] | None = None
) -> list[Requirement]:
    tags = product_tags or set()
    return [
        requirement
        for requirement in requirements
        if requirement.active
        and (
            not requirement.applicability_tags
            or bool(set(requirement.applicability_tags).intersection(tags))
        )
    ]


def attach_evidence_references(*references: str | None) -> list[str]:
    return list(dict.fromkeys(reference for reference in references if reference))


def evaluate_requirement(
    requirement: Requirement,
    *,
    answers: dict[str, str],
    profile: dict[str, Any],
    non_empty_process_steps: int,
    observations: list[dict[str, Any]],
    unavailable_types: list[str] | None = None,
) -> EvaluatedRequirement:
    rule = requirement.evaluation_rule
    status = RequirementStatus.UNKNOWN
    references: list[str] = []
    rationale = "Not enough submitted evidence is available to confirm this practice."

    if rule.get("derived") == "process_steps":
        references = ["process.steps"]
        if non_empty_process_steps >= 3:
            status = RequirementStatus.CONFIRMED
            rationale = "At least three ordered production stages were provided."
        elif non_empty_process_steps:
            status = RequirementStatus.PARTIAL
            rationale = "Some production stages were provided, but the process is incomplete."
        else:
            status = RequirementStatus.GAP
            rationale = "No production stages were provided."
    else:
        source = str(rule.get("question") or rule.get("profile_field") or "")
        value = answers.get(source) if rule.get("question") else profile.get(source)
        if value is not None:
            references = [f"answer.{source}" if rule.get("question") else f"profile.{source}"]
            for candidate_status in (
                RequirementStatus.CONFIRMED,
                RequirementStatus.PARTIAL,
                RequirementStatus.GAP,
            ):
                values = rule.get(candidate_status.value, [])
                if value in values:
                    status = candidate_status
                    rationale = {
                        RequirementStatus.CONFIRMED: "The submitted answer confirms this practice.",
                        RequirementStatus.PARTIAL: "The submitted answer shows the practice is partly in place.",
                        RequirementStatus.GAP: "The submitted answer confirms this practice is not yet in place.",
                    }[candidate_status]
                    break

    relevant_observations = [
        observation
        for observation in observations
        if observation["requirement_id"] == requirement.id
        and Decimal(str(observation["confidence"])) >= Decimal("0.50")
    ]
    if status == RequirementStatus.UNKNOWN and relevant_observations:
        strongest = max(relevant_observations, key=lambda item: item["confidence"])
        references.append(f"evidence:{strongest['id']}")
        if strongest["polarity"] == "supports":
            status = RequirementStatus.CONFIRMED
            rationale = "Submitted evidence contains a clear supporting observation."
        elif strongest["polarity"] == "concern":
            status = RequirementStatus.GAP
            rationale = "Submitted evidence contains a clear concern about this practice."

    if status == RequirementStatus.UNKNOWN and unavailable_types:
        references.extend(f"unavailable:{item}" for item in unavailable_types)

    return EvaluatedRequirement(
        requirement_id=requirement.id,
        category=requirement.category.value,
        title=requirement.title,
        weight=Decimal(requirement.weight),
        safety_critical=requirement.safety_critical,
        status=status,
        multiplier=MULTIPLIERS[status],
        evidence_references=list(dict.fromkeys(references)),
        rationale=rationale,
    )


def evaluate_all_requirements(
    requirements: list[Requirement],
    *,
    answers: dict[str, str],
    profile: dict[str, Any],
    non_empty_process_steps: int,
    observations: list[dict[str, Any]],
    unavailable_by_requirement: dict[str, list[str]] | None = None,
) -> list[EvaluatedRequirement]:
    unavailable = unavailable_by_requirement or {}
    return [
        evaluate_requirement(
            requirement,
            answers=answers,
            profile=profile,
            non_empty_process_steps=non_empty_process_steps,
            observations=observations,
            unavailable_types=unavailable.get(requirement.id),
        )
        for requirement in load_applicable_requirements(requirements)
    ]
