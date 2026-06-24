from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv


QUEUE_NAME = "agentic_hr"


def redis_queue_available() -> bool:
    load_dotenv()
    redis_url = os.getenv("HR_REDIS_URL")
    if not redis_url:
        return False
    try:
        import redis
        from rq import Queue
    except ImportError:
        return False
    try:
        connection = redis.Redis.from_url(redis_url, socket_connect_timeout=0.2, socket_timeout=0.2)
        connection.ping()
        Queue(QUEUE_NAME, connection=connection)
    except Exception:
        return False
    return True


def enqueue_batch_evaluation_job(job_id: str, request_payload: dict[str, Any]) -> bool:
    load_dotenv()
    redis_url = os.getenv("HR_REDIS_URL")
    if not redis_url:
        return False
    try:
        import redis
        from rq import Queue
    except ImportError:
        return False

    connection = redis.Redis.from_url(redis_url)
    connection.ping()
    queue = Queue(QUEUE_NAME, connection=connection)
    queue.enqueue(
        "workers.jobs.run_batch_evaluation_job",
        job_id,
        request_payload,
        job_timeout=int(os.getenv("HR_JOB_TIMEOUT_SECONDS", "1800")),
        result_ttl=int(os.getenv("HR_JOB_RESULT_TTL_SECONDS", "86400")),
        failure_ttl=int(os.getenv("HR_JOB_FAILURE_TTL_SECONDS", "86400")),
    )
    return True
