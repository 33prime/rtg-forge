"""Good LangGraph example: RAG pipeline with typed state, focused nodes,
conditional routing, error handling, and checkpointing.

Demonstrates:
- TypedDict state with annotations
- Small, focused, testable nodes
- Conditional routing with error paths
- Tool integration
- Proper prompt management
- Checkpointing for persistence
"""

from __future__ import annotations

import json
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, add_messages
from langgraph.prebuilt import ToolNode

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_RETRIES = 3

SYSTEM_PROMPT = """You are a helpful invoice assistant. Answer questions about
invoices using the provided context. If the context doesn't contain the answer,
say so clearly. Always cite specific data from the context."""

RAG_PROMPT = """Context from the knowledge base:
{context}

Based on the above context, answer the user's question. If the context doesn't
contain enough information, say so."""

# ---------------------------------------------------------------------------
# State definition — typed, documented
# ---------------------------------------------------------------------------

class RAGState(TypedDict):
    """State for the RAG pipeline."""
    messages: Annotated[list, add_messages]  # Chat history with append reducer
    context: str                              # Retrieved document context
    retry_count: int                          # Number of generation retries
    error: str | None                         # Error message, if any
    final_answer: str | None                  # Final validated answer


# ---------------------------------------------------------------------------
# Tools — focused, documented, typed
# ---------------------------------------------------------------------------

@tool
def search_invoices(query: str, limit: int = 5) -> str:
    """Search the invoice database for records matching the query.

    Args:
        query: Natural language search query
        limit: Maximum results to return (default 5)
    """
    # In production, this would query a real database/vector store
    results = [
        {"id": "inv-001", "customer": "Acme Corp", "total": 1500.00, "status": "paid"},
        {"id": "inv-002", "customer": "Acme Corp", "total": 2300.50, "status": "overdue"},
    ]
    return json.dumps(results[:limit])


tools = [search_invoices]


# ---------------------------------------------------------------------------
# Nodes — each does ONE thing
# ---------------------------------------------------------------------------

async def retrieve_context(state: RAGState) -> dict:
    """Retrieve relevant context from the knowledge base."""
    query = state["messages"][-1].content

    try:
        # In production: vector store retrieval
        # docs = await retriever.ainvoke(query)
        # context = "\n\n".join(doc.page_content for doc in docs)
        context = f"[Retrieved context for: {query}]"
        return {"context": context}
    except Exception as e:
        return {"error": f"Retrieval failed: {e}"}


async def generate_response(state: RAGState) -> dict:
    """Generate a response using the LLM with retrieved context."""
    if state.get("error"):
        return {}  # Skip — previous node errored

    user_question = state["messages"][-1].content
    rag_context = RAG_PROMPT.format(context=state["context"])

    # In production: actual LLM call
    # response = await llm.ainvoke([
    #     SystemMessage(content=SYSTEM_PROMPT),
    #     SystemMessage(content=rag_context),
    #     *state["messages"],
    # ])

    response_text = f"Based on the context, here is the answer to: {user_question}"
    response = AIMessage(content=response_text)

    return {
        "messages": [response],
        "final_answer": response.content,
    }


async def validate_response(state: RAGState) -> dict:
    """Validate the generated response for quality."""
    if state.get("error"):
        return {}

    answer = state.get("final_answer", "")

    # Validation checks
    if not answer or len(answer) < 10:
        return {
            "error": None,  # Not a fatal error
            "final_answer": None,  # Clear to trigger retry
            "retry_count": state.get("retry_count", 0) + 1,
        }

    return {}  # Validation passed, no state changes needed


async def handle_error(state: RAGState) -> dict:
    """Handle errors and produce a user-friendly response."""
    error_msg = state.get("error", "An unknown error occurred")

    return {
        "messages": [
            AIMessage(content=f"I'm sorry, I ran into an issue: {error_msg}. Please try again.")
        ],
        "final_answer": None,
        "error": None,  # Clear error after handling
    }


# ---------------------------------------------------------------------------
# Routing functions — pure, only read state
# ---------------------------------------------------------------------------

def route_after_retrieval(state: RAGState) -> str:
    """Route based on retrieval result."""
    if state.get("error"):
        return "error"
    if not state.get("context"):
        return "error"
    return "success"


def route_after_validation(state: RAGState) -> str:
    """Route based on validation result."""
    if state.get("error"):
        return "error"
    if state.get("final_answer"):
        return "valid"
    if state.get("retry_count", 0) >= MAX_RETRIES:
        return "error"
    return "retry"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_rag_graph() -> StateGraph:
    """Build and compile the RAG pipeline graph."""
    graph = StateGraph(RAGState)

    # Add nodes
    graph.add_node("retrieve", retrieve_context)
    graph.add_node("generate", generate_response)
    graph.add_node("validate", validate_response)
    graph.add_node("handle_error", handle_error)

    # Set entry point
    graph.set_entry_point("retrieve")

    # Edges: retrieve -> route -> generate or error
    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieval,
        {
            "success": "generate",
            "error": "handle_error",
        },
    )

    # Edges: generate -> validate
    graph.add_edge("generate", "validate")

    # Edges: validate -> route -> end, retry, or error
    graph.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "valid": END,
            "retry": "generate",
            "error": "handle_error",
        },
    )

    # Error handler always ends
    graph.add_edge("handle_error", END)

    # Compile with checkpointing
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------

async def main() -> None:
    graph = build_rag_graph()

    # Thread ID scopes the conversation
    config = {"configurable": {"thread_id": "user-session-001"}}

    initial_state: RAGState = {
        "messages": [HumanMessage(content="What is the total for Acme Corp invoices?")],
        "context": "",
        "retry_count": 0,
        "error": None,
        "final_answer": None,
    }

    result = await graph.ainvoke(initial_state, config=config)
    print(result["final_answer"])
