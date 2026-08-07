"""Applicability Reasoning Agent service.

Runs the plan_applicable_schemes AI operation and persists the decision.
The AI receives deterministic, DB-sourced scheme facts and reasons over them.
All outputs are whitelisted against the supplied scheme IDs before persistence.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError
from app.models import Assessment, BusinessProfile
from app.models.enums import CertificationTrack
from app.schemas.ai import ApplicabilityDecisionOutput
from app.services.ai_service import run_with_validation
from app.services.catalog_service import list_schemes_for_product


def create_business_profile(
    db: Session,
    *,
    name: str,
    business_type: str,
    years_operating: int | None,
    scale: str,
    market: list[str],
    existing_certifications: list[str],
    has_food_licence: str,
    monthly_volume_range: str | None,
    additional_info: str,
) -> BusinessProfile:
    """Persist a new business profile and return it."""
    profile = BusinessProfile(
        name=name,
        business_type=business_type,
        years_operating=years_operating,
        scale=scale,
        market=market,
        existing_certifications=existing_certifications,
        has_food_licence=has_food_licence,
        monthly_volume_range=monthly_volume_range,
        additional_info=additional_info,
        created_at=datetime.now(timezone.utc),
    )
    db.add(profile)
    db.flush()
    return profile


def _scheme_payload(scheme: Any) -> dict[str, Any]:
    """Serialise a CertificationScheme into the form sent to the AI."""
    return {
        "id": scheme.id,
        "name": scheme.name,
        "short_code": scheme.short_code,
        "track": scheme.track.value if hasattr(scheme.track, "value") else str(scheme.track),
        "mandatory_tier": scheme.mandatory_tier.value
        if hasattr(scheme.mandatory_tier, "value")
        else str(scheme.mandatory_tier),
        "applicability_rule": scheme.applicability_rule,
        "summary": scheme.summary,
        "typical_timeline_days": scheme.typical_timeline_days,
        "standard_version": scheme.standard_version,
        "catalogue_revision": scheme.catalogue_revision,
        "source_document_id": scheme.source_document_id,
        "body_name": scheme.body.name if scheme.body else "",
    }


def _validate_applicability_output(
    output: ApplicabilityDecisionOutput,
    allowed_scheme_ids: set[str],
) -> None:
    """Whitelist check: reject any scheme IDs or invalid tiers the AI invented."""
    unknown = {d.scheme_id for d in output.decisions} - allowed_scheme_ids
    if unknown:
        raise ValueError(
            f"AI returned unknown scheme IDs not in the supplied whitelist: {sorted(unknown)}"
        )
    if (
        output.recommended_path_scheme_id is not None
        and output.recommended_path_scheme_id not in allowed_scheme_ids
    ):
        raise ValueError(
            f"recommended_path_scheme_id '{output.recommended_path_scheme_id}' is not in the whitelist"
        )
    allowed_tiers = {"mandatory", "market_required", "recommended", "optional"}
    for d in output.decisions:
        if d.tier not in allowed_tiers:
            raise ValueError(f"Invalid mandatory tier '{d.tier}' returned for scheme '{d.scheme_id}'")


async def run_applicability_agent(
    db: Session,
    assessment: Assessment,
    *,
    track: CertificationTrack | None = None,
) -> ApplicabilityDecisionOutput:
    """Run the Applicability Reasoning Agent for a given assessment.

    - Infers track from the assessment when not supplied:
        - product_id is set  → PRODUCT_QUALITY (Track 1)
        - product_id is None → PROCESS_MANAGEMENT (Track 2)
    - Loads all active schemes from the DB for the resolved track.
    - Sends business profile + product context + scheme catalogue to the AI.
    - Validates that the AI only returns supplied scheme IDs.
    - Persists the decision in assessment.profile_data['applicability_decision'].
    - Sets assessment.scheme_id to the recommended path scheme.
    """
    if assessment.business_profile_id is None:
        raise AppError(
            "missing_business_profile",
            "A business profile must be saved before running the applicability check.",
            400,
        )

    business_profile = db.get(BusinessProfile, assessment.business_profile_id)
    if business_profile is None:
        raise NotFoundError("Business profile not found.")

    # Infer track when not explicitly supplied
    if track is None:
        track = (
            CertificationTrack.PRODUCT_QUALITY
            if assessment.product_id is not None
            else CertificationTrack.PROCESS_MANAGEMENT
        )

    product_id_str = str(assessment.product_id) if assessment.product_id else None
    schemes = list_schemes_for_product(db, product_id_str, track)
    if not schemes:
        raise AppError(
            "no_schemes_available",
            "No certification schemes are currently available for this product and track.",
            422,
        )

    allowed_ids = {s.id for s in schemes}
    scheme_payloads = [_scheme_payload(s) for s in schemes]

    business_profile_dict: dict[str, Any] = {
        "name": business_profile.name,
        "business_type": business_profile.business_type,
        "years_operating": business_profile.years_operating,
        "scale": business_profile.scale,
        "market": business_profile.market,
        "existing_certifications": business_profile.existing_certifications,
        "has_food_licence": business_profile.has_food_licence,
        "monthly_volume_range": business_profile.monthly_volume_range,
    }

    product_dict: dict[str, Any] = {}
    if assessment.product_id:
        from app.models import Product

        product = db.get(Product, assessment.product_id)
        if product:
            product_dict = {"id": str(product.id), "name": product.name, "slug": product.slug}

    def validate(output: ApplicabilityDecisionOutput) -> None:
        _validate_applicability_output(output, allowed_ids)

    result = await run_with_validation(
        db,
        assessment.id,
        "plan_applicable_schemes",
        lambda provider: provider.plan_applicable_schemes(
            business_profile_dict, product_dict, scheme_payloads
        ),
        validate=validate,
    )

    decision = result.output

    # Persist decision in profile_data
    profile_data = dict(assessment.profile_data or {})
    profile_data["applicability_decision"] = {
        "decisions": [d.model_dump() for d in decision.decisions],
        "overall_reasoning": decision.overall_reasoning,
        "recommended_path_scheme_id": decision.recommended_path_scheme_id,
        "provider": result.provider,
        "fallback_used": result.fallback_used,
        "run_at": datetime.now(timezone.utc).isoformat(),
    }
    assessment.profile_data = profile_data

    # Set recommended scheme on the assessment
    if decision.recommended_path_scheme_id:
        assessment.scheme_id = decision.recommended_path_scheme_id
        selected_scheme = next(
            (scheme for scheme in schemes if scheme.id == decision.recommended_path_scheme_id),
            None,
        )
        if selected_scheme is not None:
            assessment.scheme_version = selected_scheme.standard_version
            assessment.catalogue_revision = selected_scheme.catalogue_revision

    db.flush()
    return decision
