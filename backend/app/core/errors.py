from typing import Any


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__("not_found", message, 404)


class TransitionError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("invalid_transition", message, 409)


class ConfigurationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("configuration_error", message, 500)
