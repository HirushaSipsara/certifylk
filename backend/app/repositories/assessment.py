import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models import Assessment


class AssessmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, assessment: Assessment) -> Assessment:
        self.db.add(assessment)
        self.db.flush()
        return assessment

    def get(self, assessment_id: uuid.UUID, *, for_update: bool = False) -> Assessment:
        statement = select(Assessment).where(Assessment.id == assessment_id)
        if for_update:
            statement = statement.with_for_update()
        assessment = self.db.scalar(statement)
        if assessment is None:
            raise NotFoundError("Assessment not found.")
        return assessment
