"""Exception handlers mapping domain errors to JSON responses."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.core.exceptions import AppError
from app.core.logging import get_logger

logger = get_logger("app.errors")


def _error_body(error_code: str, message: str, details: dict | None = None) -> dict:
    return {
        "error_code": error_code,
        "message": message,
        "details": details or {},
    }


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Translate an :class:`AppError` into its declared status + JSON body."""
    if exc.status_code >= 500:
        logger.error(
            "app_error",
            error_code=exc.error_code,
            message=exc.message,
            path=request.url.path,
        )
    else:
        logger.info(
            "app_error",
            error_code=exc.error_code,
            message=exc.message,
            path=request.url.path,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.error_code, exc.message, exc.details),
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a 422 with the validation error details."""
    return JSONResponse(
        status_code=422,
        content=_error_body(
            "validation_error",
            "Request validation failed",
            {"errors": jsonable_encoder(exc.errors())},
        ),
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Normalise Starlette/FastAPI HTTPExceptions to the shared error shape."""
    detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body("http_error", detail),
        headers=getattr(exc, "headers", None),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all 500 handler that never leaks internals to the client."""
    logger.exception(
        "unhandled_error",
        path=request.url.path,
        error=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content=_error_body("internal_error", "An unexpected error occurred"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
