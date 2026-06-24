from __future__ import annotations

from core.persistence import SQLiteRunStore
from core.store_factory import create_run_store


def test_create_run_store_defaults_to_sqlite(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("HR_DATABASE_URL", raising=False)
    monkeypatch.setenv("HR_SQLITE_PATH", str(tmp_path / "runs.db"))

    store = create_run_store()

    assert isinstance(store, SQLiteRunStore)


def test_create_run_store_uses_sqlalchemy_for_database_url(monkeypatch) -> None:
    monkeypatch.setenv("HR_DATABASE_URL", "sqlite+pysqlite:///:memory:")

    store = create_run_store()

    assert store.__class__.__name__ == "SQLAlchemyRunStore"
