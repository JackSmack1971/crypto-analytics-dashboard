"""Application logging utilities with secret redaction."""

from __future__ import annotations

import logging
import os
import re

SECRET_NAME_RE = re.compile(r".*_(?:KEY|TOKEN)$")


class SecretFilter(logging.Filter):
    """Redact secret environment values from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for name, value in os.environ.items():
            if SECRET_NAME_RE.match(name) and value:
                message = message.replace(value, "[REDACTED]")
        record.msg = message
        record.args = ()
        return True


def configure_logging(logger: logging.Logger | None = None) -> logging.Logger:
    """Configure logging with secret redaction filter.

    Args:
        logger: Optional existing logger to configure.

    Returns:
        Configured logger instance.
    """

    log = logger or logging.getLogger("app")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.addFilter(SecretFilter())
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    return log
