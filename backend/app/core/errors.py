from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import logger
from app.schemas.error import ApiErrorResponse, utc_now


def error_payload(error_code: str, message: str, status_code: int) -> dict:
    return ApiErrorResponse(
        error_code=error_code,
        message=message,
        status_code=status_code,
        timestamp=utc_now(),
    ).model_dump(mode="json")


def api_error_response(error_code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=error_payload(error_code, message, status_code))


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        error_code = str(detail.get("error_code") or exc.__class__.__name__)
        message = str(detail.get("message") or "Request failed.")
    else:
        error_code = exc.__class__.__name__
        message = str(detail or "Request failed.")
    return api_error_response(error_code, message, exc.status_code)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Use the modern status name when available; otherwise fallback to the numeric
    # HTTP 422 code to avoid touching the deprecated Starlette alias.
    unprocessable_status = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)
    return api_error_response(
        "ValidationError",
        "Request validation failed.",
        unprocessable_status,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled server error",
        extra={"method": request.method, "endpoint": request.url.path},
        exc_info=True,
    )
    return api_error_response(
        "InternalServerError",
        "An internal server error occurred while processing your request.",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def raise_api_error(status_code: int, error_code: str, message: str) -> None:
    raise HTTPException(status_code=status_code, detail={"error_code": error_code, "message": message})
