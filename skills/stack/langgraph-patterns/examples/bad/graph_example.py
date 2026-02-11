"""BAD LangGraph example: Untyped state, hardcoded prompts, no error handling,
monolithic nodes, no checkpointing.

Problems demonstrated:
- No TypedDict state — using raw dicts
- Hardcoded prompts in node functions
- No error handling in nodes
- Monolithic node doing too much
- No conditional routing for errors
- No checkpointing
- No retry limits
- Tight coupling to specific LLM
"""

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

# No typed state — just using raw dict
# No constants for prompts or config


def do_everything(state):
    """One massive node that does retrieval, generation, and validation."""
    # No type hints on state

    # Hardcoded prompt directly in the function
    prompt = "You are a helpful assistant. Answer this question: " + state["query"]

    # Hardcoded model — can't swap for testing
    llm = ChatOpenAI(model="gpt-4", api_key="sk-hardcoded-key-here")  # API KEY IN CODE!

    # No error handling at all — if this fails, the whole graph crashes
    response = llm.invoke(prompt)

    # Doing retrieval AND generation AND validation in one node
    # This is untestable and unmaintainable
    if len(response.content) < 5:
        # No retry limit — could loop forever!
        return {"query": state["query"], "retry": True}

    # No validation of response quality

    return {
        "query": state["query"],
        "answer": response.content,
        "retry": False,
    }


def check_retry(state):
    """Routing function that also modifies state (wrong!)."""
    # BAD: Routing functions should only READ state
    state["attempt"] = state.get("attempt", 0) + 1  # Mutating state!

    if state.get("retry"):
        return "retry"
    return "done"


# BAD: No checkpointing, no error handling path
graph = StateGraph(dict)  # Untyped state!

graph.add_node("process", do_everything)
graph.set_entry_point("process")

graph.add_conditional_edges(
    "process",
    check_retry,
    {
        "retry": "process",  # No retry limit — infinite loop risk!
        "done": END,
    },
)

# No error handling node
# No checkpointing
chain = graph.compile()  # No checkpointer argument


# Usage — no thread_id, no proper state initialization
def run():
    # Raw dict, no typing
    result = chain.invoke({"query": "What are my invoices?"})
    print(result.get("answer"))
