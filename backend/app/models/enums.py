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
