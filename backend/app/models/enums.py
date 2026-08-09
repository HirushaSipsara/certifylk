from enum import Enum


class StrEnum(str, Enum):
    """String enum compatible with Python 3.10 and newer."""


class AssessmentStatus(StrEnum):
    DRAFT_PROFILE = "draft_profile"
    PROFILE_COMPLETE = "profile_complete"
    PROCESS_COMPLETE = "process_complete"
    EVIDENCE_PENDING = "evidence_pending"
    EVIDENCE_COMPLETE = "evidence_complete"
    CLARIFICATION_PENDING = "clarification_pending"
    READY_TO_SCORE = "ready_to_score"
    COMPLETED = "completed"
    FAILED = "failed"


class AssessmentPage(StrEnum):
    PROFILE = "profile"
    PROCESS = "process"
    EVIDENCE = "evidence"
    CLARIFICATION = "clarification"
    RESULT = "result"


class QuestionPage(StrEnum):
    ADAPTIVE = "adaptive"
    CLARIFICATION = "clarification"


class EvidenceKind(StrEnum):
    PHOTO = "photo"
    DOCUMENT = "document"


class EvidenceRequestStatus(StrEnum):
    REQUESTED = "requested"
    UPLOADED = "uploaded"
    UNAVAILABLE = "unavailable"
    ANALYZED = "analyzed"


class SelfAssessmentValue(StrEnum):
    YES = "yes"
    PARTIAL = "partial"
    NO = "no"
    NOT_SURE = "not_sure"


class ObservationPolarity(StrEnum):
    SUPPORTS = "supports"
    CONCERN = "concern"
    UNCLEAR = "unclear"


class RequirementStatus(StrEnum):
    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    GAP = "gap"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class RequirementCategory(StrEnum):
    HYGIENE_SANITATION = "hygiene_sanitation"
    PROCESS_CONTROL = "process_control"
    DOCUMENTATION_RECORDS = "documentation_records"
    RAW_MATERIAL_SUPPLIER = "raw_material_supplier"
    PACKAGING_LABELLING = "packaging_labelling"
    STORAGE_TRACEABILITY = "storage_traceability"


# ── New enums for certification knowledge base ────────────────────────────────


class CertificationTrack(StrEnum):
    PRODUCT_QUALITY = "product_quality"
    PROCESS_MANAGEMENT = "process_management"


class MandatoryTier(StrEnum):
    MANDATORY = "mandatory"
    MARKET_REQUIRED = "market_required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


class CostType(StrEnum):
    CERTIFYING_BODY_FEE = "certifying_body_fee"
    LAB_TESTING_FEE = "lab_testing_fee"
    BUSINESS_CAPEX = "business_capex"
    BUSINESS_OPEX = "business_opex"
