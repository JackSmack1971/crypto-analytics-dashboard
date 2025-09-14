"""Environment variable configuration for the backend service."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Typed runtime settings loaded from environment variables."""

    api_host: str
    api_port: int
    redis_url: str
    debug: bool


def _getenv(
    name: str,
    *,
    default: str | None = None,
    cast: type = str,
    required: bool = False,
):
    """Fetch an environment variable and cast it to the given type.

    Args:
        name: The environment variable name.
        default: Default value if the variable is not set.
        cast: Type to cast the variable to. Booleans accept common true values.
        required: If True, raises RuntimeError when the variable is missing.

    Returns:
        The cast value or the default when provided.
    """

    raw = os.getenv(name)
    if raw is None:
        if required:
            raise RuntimeError(f"{name} environment variable is required")
        raw = default
    if raw is None:
        return None
    if cast is bool:
        return raw.lower() in {"1", "true", "t", "yes", "on"}
    try:
        return cast(raw)
    except Exception as exc:
        raise RuntimeError(f"invalid value for {name}") from exc


def load() -> Settings:
    """Load typed settings from environment variables."""

    return Settings(
        api_host=_getenv("API_HOST", default="127.0.0.1"),
        api_port=_getenv("API_PORT", default="8000", cast=int),
        redis_url=_getenv("REDIS_URL", required=True),
        debug=_getenv("DEBUG", default="0", cast=bool),
    )
