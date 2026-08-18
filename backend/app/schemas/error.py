from datetime import datetime, timezone
from pydantic import BaseModel


class ApiErrorResponse(BaseModel):
    error_code: str
    message: str
    status_code: int
    timestamp: datetime


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
