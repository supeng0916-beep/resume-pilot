from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from core.state import WorkflowState
from graph.routing import (
    route_after_evidence_audit,
    route_after_review_supervisor,
    route_after_validation,
)
from nodes.consensus_agent import consensus_agent_node
from nodes.critic_agent import critic_agent_node
from nodes.document_parser import document_parser_node
from nodes.evidence_auditor import evidence_auditor_node
from nodes.human_review import human_review_node
from nodes.jd_extractor import jd_extractor_node
from nodes.matcher import matcher_node
from nodes.parallel_specialists import parallel_specialists_node
from nodes.report_writer import report_writer_node
from nodes.resume_extractor import resume_extractor_node
from nodes.risk_evaluator import risk_evaluator_node
from nodes.rubric_selector import rubric_selector_node
from nodes.supervisor import supervisor_node, supervisor_review_router_node
from nodes.validator import validator_node


def build_workflow():
    graph = StateGraph(WorkflowState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("supervisor_review_router", supervisor_review_router_node)
    graph.add_node("document_parser", document_parser_node)
    graph.add_node("resume_extractor", resume_extractor_node)
    graph.add_node("jd_extractor", jd_extractor_node)
    graph.add_node("validator", validator_node)
    graph.add_node("parallel_specialists", parallel_specialists_node)
    graph.add_node("evidence_auditor", evidence_auditor_node)
    graph.add_node("critic_agent", critic_agent_node)
    graph.add_node("consensus_agent", consensus_agent_node)
    graph.add_node("matcher", matcher_node)
    graph.add_node("risk_evaluator", risk_evaluator_node)
    graph.add_node("rubric_selector", rubric_selector_node)
    graph.add_node("report_writer", report_writer_node)
    graph.add_node("human_review", human_review_node)

    graph.add_edge(START, "supervisor")
    graph.add_edge("supervisor", "document_parser")
    graph.add_edge("document_parser", "resume_extractor")
    graph.add_edge("resume_extractor", "jd_extractor")
    graph.add_edge("jd_extractor", "validator")
    graph.add_conditional_edges(
        "validator",
        route_after_validation,
        {
            "retry_resume_extractor": "resume_extractor",
            "continue_to_matcher": "parallel_specialists",
            "fail_to_report": "report_writer",
        },
    )
    graph.add_edge("parallel_specialists", "rubric_selector")
    graph.add_edge("rubric_selector", "matcher")
    graph.add_edge("matcher", "risk_evaluator")
    graph.add_edge("risk_evaluator", "supervisor_review_router")
    graph.add_conditional_edges(
        "supervisor_review_router",
        route_after_review_supervisor,
        {
            "evidence_auditor": "evidence_auditor",
            "critic_agent": "critic_agent",
            "consensus_agent": "consensus_agent",
        },
    )
    graph.add_conditional_edges(
        "evidence_auditor",
        route_after_evidence_audit,
        {
            "critic_agent": "critic_agent",
            "consensus_agent": "consensus_agent",
        },
    )
    graph.add_edge("critic_agent", "consensus_agent")
    graph.add_edge("consensus_agent", "report_writer")
    graph.add_edge("report_writer", "human_review")
    graph.add_edge("human_review", END)

    return graph.compile()
