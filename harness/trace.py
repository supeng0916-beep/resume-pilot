from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.state import WorkflowState


def add_trace(
    state: WorkflowState,
    node_name: str,
    output_summary: str,
    extra: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    trace = list(state.get("trace", []))
    trace.append(
        {
            "node": node_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "output_summary": output_summary,
            "extra": extra or {},
        }
    )
    return trace
