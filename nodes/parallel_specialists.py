from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter
from typing import Callable

from core.state import WorkflowState
from harness.trace import add_trace
from nodes.candidate_analyst import candidate_analyst_node
from nodes.job_analyst import job_analyst_node
from nodes.memory_retriever import memory_retriever_node


SpecialistNode = Callable[[WorkflowState], WorkflowState]


SPECIALIST_NODES: dict[str, SpecialistNode] = {
    "candidate_analyst": candidate_analyst_node,
    "job_analyst": job_analyst_node,
    "memory_agent": memory_retriever_node,
}

DEFAULT_SPECIALIST_ROUTE = ["candidate_analyst", "job_analyst"]


def _merge_specialist_update(base: WorkflowState, update: WorkflowState) -> None:
    for key, value in update.items():
        if key == "trace":
            merged_trace = list(base.get("trace") or [])
            known = {
                (item.get("node"), item.get("output_summary"))
                for item in merged_trace
                if isinstance(item, dict)
            }
            for item in value or []:
                if not isinstance(item, dict):
                    continue
                marker = (item.get("node"), item.get("output_summary"))
                if marker not in known:
                    merged_trace.append(item)
                    known.add(marker)
            base["trace"] = merged_trace
            continue
        if key in {"agent_outputs", "agent_metrics"}:
            merged = dict(base.get(key) or {})
            merged.update(value or {})
            base[key] = merged
        else:
            base[key] = value


def parallel_specialists_node(state: WorkflowState) -> WorkflowState:
    started = perf_counter()
    active_agents = set(state.get("active_agents") or DEFAULT_SPECIALIST_ROUTE)
    selected_nodes = {
        name: node
        for name, node in SPECIALIST_NODES.items()
        if name in active_agents
    }
    merged: WorkflowState = {
        "agent_outputs": dict(state.get("agent_outputs") or {}),
        "agent_metrics": dict(state.get("agent_metrics") or {}),
    }
    completed_agents: list[str] = []

    if not selected_nodes:
        selected_nodes = {
            name: SPECIALIST_NODES[name]
            for name in DEFAULT_SPECIALIST_ROUTE
        }

    with ThreadPoolExecutor(max_workers=len(selected_nodes)) as executor:
        futures = {
            executor.submit(node, state): name
            for name, node in selected_nodes.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            update = future.result()
            _merge_specialist_update(merged, update)
            completed_agents.append(name)

    duration_ms = int((perf_counter() - started) * 1000)
    specialist_execution = {
        "mode": "parallel",
        "agents": sorted(completed_agents),
        "duration_ms": duration_ms,
    }
    merged.update(
        {
            "specialist_execution": specialist_execution,
            "current_step": "parallel_specialists",
            "trace": add_trace(
                {**state, "trace": merged.get("trace", [])},
                "parallel_specialists",
                "Ran supervisor-selected specialist agents in parallel.",
                specialist_execution,
            ),
        }
    )
    return merged
