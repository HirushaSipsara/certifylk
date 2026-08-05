from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class MessageResponse(BaseModel):
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
