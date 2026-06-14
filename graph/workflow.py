from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from core.state import WorkflowState
from graph.routing import route_after_validation
from nodes.candidate_analyst import candidate_analyst_node
from nodes.document_parser import document_parser_node
from nodes.human_review import human_review_node
from nodes.jd_extractor import jd_extractor_node
from nodes.job_analyst import job_analyst_node
from nodes.matcher import matcher_node
from nodes.memory_retriever import memory_retriever_node
from nodes.report_writer import report_writer_node
from nodes.reporting_agent import reporting_agent_node
from nodes.resume_extractor import resume_extractor_node
from nodes.risk_evaluator import risk_evaluator_node
from nodes.rubric_selector import rubric_selector_node
from nodes.supervisor import supervisor_node
from nodes.validator import validator_node


def build_workflow():
    graph = StateGraph(WorkflowState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("document_parser", document_parser_node)
    graph.add_node("resume_extractor", resume_extractor_node)
    graph.add_node("jd_extractor", jd_extractor_node)
    graph.add_node("validator", validator_node)
    graph.add_node("candidate_analyst", candidate_analyst_node)
    graph.add_node("job_analyst", job_analyst_node)
    graph.add_node("matcher", matcher_node)
    graph.add_node("risk_evaluator", risk_evaluator_node)
    graph.add_node("memory_retriever", memory_retriever_node)
    graph.add_node("rubric_selector", rubric_selector_node)
    graph.add_node("reporting_agent", reporting_agent_node)
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
            "continue_to_matcher": "candidate_analyst",
            "fail_to_report": "report_writer",
        },
    )
    graph.add_edge("candidate_analyst", "job_analyst")
    graph.add_edge("job_analyst", "memory_retriever")
    graph.add_edge("memory_retriever", "rubric_selector")
    graph.add_edge("rubric_selector", "matcher")
    graph.add_edge("matcher", "risk_evaluator")
    graph.add_edge("risk_evaluator", "reporting_agent")
    graph.add_edge("reporting_agent", "report_writer")
    graph.add_edge("report_writer", "human_review")
    graph.add_edge("human_review", END)

    return graph.compile()
