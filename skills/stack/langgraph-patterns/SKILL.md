# LangGraph Patterns

Patterns for building reliable, maintainable AI agent workflows with LangGraph. Graphs should have typed state, focused nodes, explicit routing, and proper error handling.

---

## Typed State

Every graph MUST define its state as a `TypedDict`. The state is the single source of truth flowing through the graph.

```python
from typing import TypedDict, Annotated
from langgraph.graph import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # Chat history with reducer
    context: str                              # Retrieved context
    plan: list[str]                           # Action plan steps
    current_step: int                         # Progress tracker
    error: str | None                         # Error state
    final_answer: str | None                  # Output
```

### State Rules

1. Use `TypedDict` — never raw dicts
2. Use `Annotated` with reducers for append-only fields (like messages)
3. Include an `error` field for error propagation
4. Keep state flat — avoid deeply nested structures
5. Every field should have a clear purpose documented

---

## Node Design

Each node is a function that takes state, performs ONE operation, and returns a state update.

```python
async def retrieve_context(state: AgentState) -> dict:
    """Retrieve relevant context from the knowledge base."""
    query = state["messages"][-1].content

    try:
        docs = await retriever.ainvoke(query)
        context = "\n\n".join(doc.page_content for doc in docs)
        return {"context": context}
    except RetrieverError as e:
        return {"error": f"Context retrieval failed: {e}"}


async def generate_response(state: AgentState) -> dict:
    """Generate a response using the LLM with retrieved context."""
    if state.get("error"):
        return {}  # Skip if previous node errored

    prompt = RESPONSE_PROMPT.format(
        context=state["context"],
        question=state["messages"][-1].content,
    )

    response = await llm.ainvoke([
        SystemMessage(content=prompt),
        *state["messages"],
    ])

    return {"messages": [response], "final_answer": response.content}
```

### Node Rules

1. Each node does ONE thing (retrieve, generate, validate, etc.)
2. Nodes return partial state updates (only the fields they modify)
3. Nodes handle their own errors and set the `error` field
4. Nodes check for previous errors and skip gracefully
5. Nodes are async when they do I/O
6. Nodes are independently testable

---

## Graph Construction

Build graphs with explicit edges and clear flow:

```python
from langgraph.graph import StateGraph, END

def build_rag_graph() -> StateGraph:
    """Build a RAG pipeline graph."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("retrieve", retrieve_context)
    graph.add_node("generate", generate_response)
    graph.add_node("validate", validate_response)
    graph.add_node("handle_error", handle_error)

    # Set entry point
    graph.set_entry_point("retrieve")

    # Add edges
    graph.add_edge("retrieve", "check_retrieval")
    graph.add_conditional_edges(
        "check_retrieval",
        route_after_retrieval,
        {
            "success": "generate",
            "error": "handle_error",
        },
    )
    graph.add_edge("generate", "validate")
    graph.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "valid": END,
            "invalid": "generate",  # Retry
            "error": "handle_error",
        },
    )
    graph.add_edge("handle_error", END)

    return graph.compile()
```

---

## Conditional Routing

Use routing functions to direct flow based on state:

```python
def route_after_retrieval(state: AgentState) -> str:
    """Route based on retrieval result."""
    if state.get("error"):
        return "error"
    if not state.get("context"):
        return "error"
    return "success"


def route_after_validation(state: AgentState) -> str:
    """Route based on validation result."""
    if state.get("error"):
        return "error"
    if state.get("validation_passed"):
        return "valid"
    if state.get("current_step", 0) >= MAX_RETRIES:
        return "error"
    return "invalid"
```

### Routing Rules

1. Routing functions are pure — they only read state, never modify it
2. Return string keys that match the conditional edge mapping
3. Always include an error route
4. Add retry limits to prevent infinite loops
5. Log routing decisions for debugging

---

## Tool Calling

Integrate tools through LangGraph's tool node pattern:

```python
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

@tool
def search_database(query: str, limit: int = 10) -> str:
    """Search the invoice database for matching records.

    Args:
        query: Search query string
        limit: Maximum number of results to return
    """
    results = db.search(query, limit=limit)
    return json.dumps([r.to_dict() for r in results])


@tool
def calculate_total(invoice_id: str) -> str:
    """Calculate the total for an invoice including tax.

    Args:
        invoice_id: The UUID of the invoice
    """
    invoice = db.get_invoice(invoice_id)
    total = sum(li.quantity * li.unit_price for li in invoice.line_items)
    tax = total * Decimal("0.08")
    return json.dumps({"subtotal": str(total), "tax": str(tax), "total": str(total + tax)})


# Create tool node
tools = [search_database, calculate_total]
tool_node = ToolNode(tools)

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)
```

### Tool Rules

1. Tools have clear, descriptive docstrings (the LLM reads them)
2. Tools return strings (serialized results)
3. Tools handle their own errors and return error messages
4. Tools are typed and validated
5. Keep tools focused — one action per tool

---

## Checkpointing

Use checkpointing for long-running graphs and human-in-the-loop patterns:

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver

# Development: in-memory checkpointing
memory = MemorySaver()
graph = build_graph().compile(checkpointer=memory)

# Production: persistent checkpointing
checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
graph = build_graph().compile(checkpointer=checkpointer)

# Invoke with thread_id for session persistence
config = {"configurable": {"thread_id": "user-session-123"}}
result = await graph.ainvoke(initial_state, config=config)

# Resume from checkpoint
result = await graph.ainvoke(None, config=config)  # Continues from last state
```

### Checkpointing Rules

1. Always use checkpointing in production
2. Use `thread_id` to scope state per conversation/user
3. Use PostgresSaver or equivalent for persistence across restarts
4. Clean up old checkpoints periodically

---

## Error Handling in Graphs

Design explicit error paths, not try/except around the whole graph:

```python
async def handle_error(state: AgentState) -> dict:
    """Handle errors gracefully and produce a user-friendly response."""
    error_msg = state.get("error", "An unknown error occurred")

    return {
        "messages": [AIMessage(content=f"I encountered an issue: {error_msg}. Please try again.")],
        "final_answer": None,
    }
```

### Error Handling Rules

1. Every graph has a dedicated error-handling node
2. Nodes set `state["error"]` instead of raising exceptions
3. Routing functions check for errors and redirect to error handler
4. Error handler produces a user-friendly message
5. Errors are logged with context (which node, what input)

---

## Prompt Management

Never hardcode prompts in node functions. Use templates with clear variables:

```python
RETRIEVAL_PROMPT = """You are a helpful assistant answering questions about invoices.

Context from the knowledge base:
{context}

User question: {question}

Instructions:
- Answer based ONLY on the provided context
- If the context doesn't contain the answer, say so
- Cite specific parts of the context in your answer
"""

# In the node:
prompt = RETRIEVAL_PROMPT.format(
    context=state["context"],
    question=state["messages"][-1].content,
)
```

### Prompt Rules

1. Prompts are module-level constants or loaded from files
2. Variables use `{name}` format for `.format()` substitution
3. Prompts include clear instructions and constraints
4. System prompts are separate from user prompts
5. Prompts are versioned alongside code
