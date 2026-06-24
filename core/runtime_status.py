from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeStatus:
    queue_backend: str
    redis_configured: bool
    redis_available: bool
    redis_message: str

    def as_dict(self) -> dict[str, object]:
        return {
            "queue_backend": self.queue_backend,
            "redis_configured": self.redis_configured,
            "redis_available": self.redis_available,
            "redis_message": self.redis_message,
        }


def get_runtime_status() -> RuntimeStatus:
    redis_url = os.getenv("HR_REDIS_URL")
    if not redis_url:
        return RuntimeStatus(
            queue_backend="fastapi_background_tasks",
            redis_configured=False,
            redis_available=False,
            redis_message="HR_REDIS_URL is not configured.",
        )

    try:
        import redis  # type: ignore[import-untyped]
    except ImportError:
        return RuntimeStatus(
            queue_backend="fastapi_background_tasks",
            redis_configured=True,
            redis_available=False,
            redis_message="redis package is not installed.",
        )

    try:
        client = redis.Redis.from_url(redis_url, socket_connect_timeout=0.2, socket_timeout=0.2)
        client.ping()
    except Exception as exc:
        return RuntimeStatus(
            queue_backend="fastapi_background_tasks",
            redis_configured=True,
            redis_available=False,
            redis_message=f"Redis is configured but unavailable: {exc}",
        )

    return RuntimeStatus(
        queue_backend="redis_ready",
        redis_configured=True,
        redis_available=True,
        redis_message="Redis connection is available.",
    )
