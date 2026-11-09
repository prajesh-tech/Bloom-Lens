import threading
import time
from collections import deque

from fastapi import HTTPException
from starlette.responses import JSONResponse
from app.core.config import settings


class UploadLimiter:
    def __init__(self):
        self.entries = {}
        self.lock = threading.Lock()

    def check(self, principal: str, limit: int | None = None) -> None:
        now = time.monotonic()
        with self.lock:
            self.entries = {key: values for key, values in self.entries.items() if values and values[-1] > now - 60}
            values = self.entries.setdefault(principal, deque())
            while values and values[0] <= now - 60:
                values.popleft()
            if len(values) >= (limit or settings.UPLOAD_RATE_LIMIT_PER_MINUTE) or len(self.entries) > 10000:
                raise HTTPException(429, detail={'error_code': 'UploadRateLimited', 'message': 'Too many uploads; retry in one minute.'}, headers={'Retry-After': '60'})
            values.append(now)


upload_limiter = UploadLimiter()


class UploadBodyLimitMiddleware:
    """Bound multipart bodies before parsing/spooling, including chunked requests."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['path'] != f'{settings.API_V1_STR}/papers/upload':
            return await self.app(scope, receive, send)
        limit = settings.MAX_REQUEST_BODY_SIZE_MB * 1024 * 1024
        headers = dict(scope.get('headers', []))
        try:
            length = int(headers.get(b'content-length', b'0'))
        except ValueError:
            length = limit + 1
        if length > limit:
            return await JSONResponse({'error_code': 'RequestBodyTooLarge', 'message': 'Upload request body exceeds the limit.'}, status_code=413)(scope, receive, send)
        received = 0

        async def bounded_receive():
            nonlocal received
            message = await receive()
            received += len(message.get('body', b''))
            if received > limit:
                raise HTTPException(413, detail={'error_code': 'RequestBodyTooLarge', 'message': 'Upload request body exceeds the limit.'})
            return message

        await self.app(scope, bounded_receive, send)
