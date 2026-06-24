from __future__ import annotations

import os

import redis
from dotenv import load_dotenv
from rq import Queue, Worker

from core.job_queue import QUEUE_NAME


def main() -> None:
    load_dotenv()
    redis_url = os.getenv("HR_REDIS_URL")
    if not redis_url:
        raise SystemExit("HR_REDIS_URL is required to start the RQ worker.")

    connection = redis.Redis.from_url(redis_url)
    queue = Queue(QUEUE_NAME, connection=connection)
    worker = Worker([queue], connection=connection)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
