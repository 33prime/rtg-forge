"""LangGraph pipeline definition for ICP signal extraction.

Flow:
  extract_signals → generate_embeddings → route_signals
    → [has_outliers?] → handle_outliers → notify → END
                     → notify → END
"""

from langgraph.graph import StateGraph, END

from .state import PipelineState
from .nodes import extract_signals, generate_embeddings, route_signals, handle_outliers, send_notifications


def has_outliers(state: PipelineState) -> bool:
    return len(state.get("outlier_indices", [])) > 0


def build_pipeline():
    graph = StateGraph(PipelineState)

    graph.add_node("extract_signals", extract_signals)
    graph.add_node("generate_embeddings", generate_embeddings)
    graph.add_node("route_signals", route_signals)
    graph.add_node("handle_outliers", handle_outliers)
    graph.add_node("notify", send_notifications)

    graph.set_entry_point("extract_signals")
    graph.add_edge("extract_signals", "generate_embeddings")
    graph.add_edge("generate_embeddings", "route_signals")
    graph.add_conditional_edges(
        "route_signals",
        has_outliers,
        {True: "handle_outliers", False: "notify"},
    )
    graph.add_edge("handle_outliers", "notify")
    graph.add_edge("notify", END)

    return graph.compile()
