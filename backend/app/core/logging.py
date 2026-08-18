import logging
import sys
from app.core.config import settings


SENSITIVE_KEYS = ("api_key", "password", "token", "secret", "authorization")


class SecretRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        lowered = message.lower()
        if any(key in lowered for key in SENSITIVE_KEYS):
            record.msg = "[redacted sensitive log message]"
            record.args = ()
        return True


def setup_logging() -> logging.Logger:
    """Configures structured application logging."""
    logger = logging.getLogger("bloomlens")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(SecretRedactionFilter())
        logger.addHandler(handler)

    return logger


logger = setup_logging()
