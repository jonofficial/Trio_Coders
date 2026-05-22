from langgraph.graph import StateGraph, END
from backend.graph.state import FDAState

from backend.graph.nodes.ingest import ingest_node
from backend.graph.nodes.validate import validate_node
from backend.graph.nodes.process import process_node
from backend.graph.nodes.aggregate import aggregate_node
from backend.graph.nodes.pyramid_calc import pyramid_calc_node
from backend.graph.nodes.rule_engine import rule_engine_node
from backend.graph.nodes.decision import decision_node
from backend.graph.nodes.r3_llm import r3_llm_node
from backend.graph.nodes.r4_llm import r4_llm_node
from backend.graph.nodes.recommendation import recommendation_node
from backend.graph.nodes.output import output_node


def route_after_decision(state: FDAState) -> str:
    """
    Routes the workflow after the decision node.
    If the decision flag is True, routes to the LLM-powered R3 node.
    Otherwise, bypasses LLM and goes straight to recommendations.
    """
    if getattr(state, "decision_flag", False):
        return "r3_llm"
    return "recommendation"

def build_fda_graph():
    """
    Builds and compiles the FDA LangGraph.
    """
    workflow = StateGraph(FDAState)
    
    # ── Add Nodes ──────────────────────────────────────────────
    workflow.add_node("ingest", ingest_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("process", process_node)
    workflow.add_node("aggregate", aggregate_node)
    workflow.add_node("pyramid_calc", pyramid_calc_node)
    workflow.add_node("rule_engine", rule_engine_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("r3_llm", r3_llm_node)
    workflow.add_node("r4_llm", r4_llm_node)
    workflow.add_node("recommendation", recommendation_node)
    workflow.add_node("output", output_node)
    
    # ── Define Deterministic Edges ─────────────────────────────
    workflow.set_entry_point("ingest")
    workflow.add_edge("ingest", "validate")
    workflow.add_edge("validate", "process")
    workflow.add_edge("process", "aggregate")
    workflow.add_edge("aggregate", "pyramid_calc")
    workflow.add_edge("pyramid_calc", "rule_engine")
    workflow.add_edge("rule_engine", "decision")
    
    # ── Define Conditional Routing ─────────────────────────────
    workflow.add_conditional_edges(
        "decision",
        route_after_decision,
        {
            "r3_llm": "r3_llm",
            "recommendation": "recommendation"
        }
    )
    
    # ── Complete the flow ──────────────────────────────────────
    workflow.add_edge("r3_llm", "r4_llm")
    workflow.add_edge("r4_llm", "recommendation")
    workflow.add_edge("recommendation", "output")
    workflow.add_edge("output", END)
    
    return workflow.compile()
