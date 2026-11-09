import json
import logging
import sys
from datetime import datetime, timezone
from urllib.parse import unquote, urlsplit
from app.core.config import settings

_STANDARD_FIELDS = set(logging.makeLogRecord({}).__dict__) | {'message', 'asctime'}


def _redact(value):
    secrets = [settings.API_KEY, settings.GEMINI_API_KEY]
    try:
        secrets.append(unquote(urlsplit(settings.DATABASE_URL).password or ''))
    except ValueError:
        pass
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, '[REDACTED]')
        return value
    if isinstance(value, dict):
        return {key: _redact(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_redact(item) for item in value]
    return value


class SecretRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg, record.args = _redact(record.getMessage()), ()
        return True


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {'timestamp': datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
                'level': record.levelname, 'logger': record.name, 'message': _redact(record.getMessage())}
        data.update({key: _redact(value) for key, value in record.__dict__.items() if key not in _STANDARD_FIELDS})
        if record.exc_info:
            data['exception'] = _redact(self.formatException(record.exc_info))
        return json.dumps(data, default=str)


def setup_logging() -> logging.Logger:
    logger = logging.getLogger('bloomlens')
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonLogFormatter())
        handler.addFilter(SecretRedactionFilter())
        logger.addHandler(handler)
    return logger


logger = setup_logging()
