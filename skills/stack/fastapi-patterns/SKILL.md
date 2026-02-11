# FastAPI Patterns

Patterns for building clean, performant, and well-structured FastAPI applications. Routes are thin — they validate input, call services, and return typed responses.

---

## Async Routes

All route handlers that perform I/O (database, HTTP calls, file operations) MUST be `async def`. Use `def` only for purely CPU-bound synchronous operations.

```python
# YES — async for I/O
@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: UUID, service: InvoiceService = Depends(get_invoice_service)) -> InvoiceResponse:
    invoice = await service.get_invoice(invoice_id)
    return InvoiceResponse.from_domain(invoice)

# NO — sync function doing I/O blocks the event loop
@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id, db=None):
    result = db.execute("SELECT * FROM invoices WHERE id = %s", (invoice_id,))
    return result
```

---

## Dependency Injection with Depends()

Use `Depends()` for ALL cross-cutting concerns: database sessions, authentication, services, configuration.

```python
# Dependencies defined as factories
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    return await authenticate_user(token, db)

def get_invoice_service(
    db: AsyncSession = Depends(get_db_session),
) -> InvoiceService:
    repo = PostgresInvoiceRepository(db)
    notifier = EmailNotificationService()
    return InvoiceService(repo=repo, notifier=notifier)
```

### Depends Rules

1. Route handlers never instantiate services directly
2. Dependencies can depend on other dependencies (composable)
3. Use `yield` dependencies for cleanup (db sessions, file handles)
4. Common dependencies go in `api/dependencies.py`
5. Auth dependencies are reusable across routers

---

## Pydantic Request/Response Models

Every route MUST use Pydantic models for request bodies and responses. Never accept or return raw dicts.

```python
class CreateInvoiceRequest(BaseModel):
    customer_id: UUID
    line_items: list[LineItemRequest]

    model_config = ConfigDict(strict=True)

class LineItemRequest(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)

class InvoiceResponse(BaseModel):
    id: UUID
    customer_id: UUID
    status: InvoiceStatus
    subtotal: Decimal
    line_items: list[LineItemResponse]
    created_at: datetime

    @classmethod
    def from_domain(cls, invoice: Invoice) -> InvoiceResponse:
        return cls(
            id=invoice.id,
            customer_id=invoice.customer_id,
            status=invoice.status,
            subtotal=invoice.subtotal,
            line_items=[LineItemResponse.from_domain(li) for li in invoice.line_items],
            created_at=invoice.created_at,
        )
```

### Model Rules

- Request models validate input (use `Field()` constraints)
- Response models shape output (use `from_domain()` class methods)
- Never expose internal domain models directly as API responses
- Use `model_config = ConfigDict(strict=True)` to prevent type coercion
- Separate request and response models even if they look similar

---

## HTTP Status Codes

Use the correct status code for every response. FastAPI makes this easy with the `status_code` parameter.

```python
@router.post("/invoices", status_code=status.HTTP_201_CREATED)
async def create_invoice(
    request: CreateInvoiceRequest,
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceResponse:
    invoice = await service.create_invoice(request.to_domain())
    return InvoiceResponse.from_domain(invoice)

@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: UUID,
    service: InvoiceService = Depends(get_invoice_service),
) -> None:
    await service.delete_invoice(invoice_id)
```

### Status Code Guide

| Operation | Success Code | Error Code |
|---|---|---|
| GET single | 200 | 404 |
| GET list | 200 | — |
| POST create | 201 | 400/409/422 |
| PUT/PATCH update | 200 | 400/404/409 |
| DELETE | 204 | 404 |

---

## Exception Handlers

Map domain exceptions to HTTP responses using exception handlers. Route handlers should NOT contain try/except for domain errors.

```python
# In api/exception_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse

async def invoice_not_found_handler(request: Request, exc: InvoiceNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": "not_found", "message": str(exc), "invoice_id": str(exc.invoice_id)},
    )

async def invoice_already_paid_handler(request: Request, exc: InvoiceAlreadyPaidError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"error": "conflict", "message": str(exc)},
    )

# In main.py
app.add_exception_handler(InvoiceNotFoundError, invoice_not_found_handler)
app.add_exception_handler(InvoiceAlreadyPaidError, invoice_already_paid_handler)
```

This keeps route handlers clean — they just call the service and return the result. Errors are handled globally.

---

## Background Tasks

Use FastAPI's `BackgroundTasks` for fire-and-forget operations that shouldn't block the response.

```python
@router.post("/invoices/{invoice_id}/send", status_code=status.HTTP_202_ACCEPTED)
async def send_invoice(
    invoice_id: UUID,
    background_tasks: BackgroundTasks,
    service: InvoiceService = Depends(get_invoice_service),
) -> dict[str, str]:
    invoice = await service.get_invoice(invoice_id)
    background_tasks.add_task(service.send_invoice_email, invoice)
    return {"status": "accepted", "message": "Invoice is being sent"}
```

Use background tasks for: email sending, webhook delivery, audit logging, cache warming. Do NOT use them for critical operations that must succeed (use a task queue instead).

---

## Middleware

Use middleware for cross-cutting concerns that apply to every request.

```python
@app.middleware("http")
async def add_request_id(request: Request, call_next: Callable) -> Response:
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

Common middleware: request ID injection, timing/logging, CORS, rate limiting, tenant extraction.

---

## Router Organization

```
api/
  main.py                # App factory, middleware, exception handlers
  dependencies.py        # Shared Depends() factories
  routes/
    invoices.py          # Invoice router
    customers.py         # Customer router
    health.py            # Health check router
```

Each router is created with a prefix and tags:

```python
router = APIRouter(prefix="/invoices", tags=["invoices"])
```

Mount routers in the app factory:

```python
app.include_router(invoices.router)
app.include_router(customers.router)
```
