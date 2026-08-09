import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import router
from app.core.config import get_settings
from app.core.errors import AppError

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("certifylk.api")

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "SLS-related food certification preparation readiness for small Sri Lankan "
        "food manufacturers. This API does not issue or guarantee certification."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def request_context(request: Request, call_next: Callable[[Request], Awaitable[Any]]) -> Any:
    supplied = request.headers.get("X-Request-ID", "")
    request_id = (
        supplied if 0 < len(supplied) <= 100 and supplied.isprintable() else str(uuid.uuid4())
    )
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_complete method=%s path=%s status=%s latency_ms=%s request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        int((time.perf_counter() - started) * 1000),
        request_id,
    )
    return response


def error_payload(
    request: Request,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, object]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
        }
    }


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(request, exc.code, exc.message, exc.details),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {
            "field": ".".join(str(part) for part in error["loc"] if part != "body"),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=error_payload(request, "validation_error", "Submitted data is invalid.", details),
    )


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(request, "http_error", str(exc.detail)),
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_error path=%s request_id=%s",
        request.url.path,
        getattr(request.state, "request_id", "unknown"),
    )
    return JSONResponse(
        status_code=500,
        content=error_payload(
            request, "internal_error", "An unexpected error occurred. Please retry."
        ),
    )


app.include_router(router, prefix=settings.api_v1_prefix)
