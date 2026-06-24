from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from core.persistence import DEFAULT_DB_PATH, SQLiteRunStore
from core.sqlalchemy_store import SQLAlchemyRunStore


def create_run_store() -> Any:
    load_dotenv()
    database_url = os.getenv("HR_DATABASE_URL") or os.getenv("DATABASE_URL")
    if database_url:
        return SQLAlchemyRunStore(database_url)

    sqlite_path = Path(os.getenv("HR_SQLITE_PATH") or DEFAULT_DB_PATH)
    return SQLiteRunStore(sqlite_path)
