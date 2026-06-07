from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from core.state import WorkflowState
from graph.routing import route_after_validation
from nodes.document_parser import document_parser_node
from nodes.jd_extractor import jd_extractor_node
from nodes.matcher import matcher_node
from nodes.orchestrator import orchestrator_node
from nodes.report_writer import report_writer_node
from nodes.resume_extractor import resume_extractor_node
from nodes.risk_evaluator import risk_evaluator_node
from nodes.rubric_selector import rubric_selector_node
from nodes.validator import validator_node


def build_workflow():
    graph = StateGraph(WorkflowState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("document_parser", document_parser_node)
    graph.add_node("resume_extractor", resume_extractor_node)
    graph.add_node("jd_extractor", jd_extractor_node)
    graph.add_node("validator", validator_node)
    graph.add_node("matcher", matcher_node)
    graph.add_node("risk_evaluator", risk_evaluator_node)
    graph.add_node("rubric_selector", rubric_selector_node)
    graph.add_node("report_writer", report_writer_node)

    graph.add_edge(START, "orchestrator")
    graph.add_edge("orchestrator", "document_parser")
    graph.add_edge("document_parser", "resume_extractor")
    graph.add_edge("resume_extractor", "jd_extractor")
    graph.add_edge("jd_extractor", "validator")
    graph.add_conditional_edges(
        "validator",
        route_after_validation,
        {
            "retry_resume_extractor": "resume_extractor",
            "continue_to_matcher": "rubric_selector",
            "fail_to_report": "report_writer",
        },
    )
    graph.add_edge("rubric_selector", "matcher")
    graph.add_edge("matcher", "risk_evaluator")
    graph.add_edge("risk_evaluator", "report_writer")
    graph.add_edge("report_writer", END)

    return graph.compile()
