# Forge-Ready Modules

Build every backend feature as a self-contained module from the start. The goal: when it's time to extract a module into RTG Forge, it's a clean copy — not a refactor.

This skill applies to **every** Python/FastAPI feature you build, whether or not it's destined for the forge. The patterns here produce better code regardless.

---

## The Six-File Rule

Every feature gets six files minimum. No exceptions, even for "small" features.

```
feature_name/
├── __init__.py    # ModuleInfo export — the module's identity
├── router.py      # FastAPI routes — thin, no logic
├── service.py     # Business logic — no framework imports
├── models.py      # Pydantic schemas — request, response, internal
├── config.py      # Settings via pydantic-settings
└── migrations/
    └── 001_create_tables.sql
```

### Why This Matters

If business logic lives in `router.py`, you can't extract the module without untangling HTTP concerns from domain logic. If models are defined inline, you can't reuse them. If config uses raw `os.getenv`, the next project has to reverse-engineer what environment variables are needed.

Six files means six clean boundaries. Each one is extractable independently.

---

## File-by-File Rules

### `__init__.py` — Module Identity

Every module exports a `module_info` object. This is the entry point for discovery and registration.

```python
from dataclasses import dataclass
from fastapi import APIRouter

@dataclass
class ModuleInfo:
    name: str
    version: str
    description: str
    router: APIRouter
    prefix: str
    tags: list[str]

from .router import router

module_info = ModuleInfo(
    name="invoice_processing",
    version="0.1.0",
    description="Invoice creation, validation, and payment tracking",
    router=router,
    prefix="/api/v1/invoices",
    tags=["invoices"],
)
```

Rules:
- `name` matches the directory name, always `snake_case`
- `prefix` follows `/api/v1/{domain}` convention
- `version` starts at `0.1.0` for new modules

### `router.py` — Thin Routes

Routes do three things: validate input, call the service, return a typed response. Nothing else.

```python
from fastapi import APIRouter, Depends, HTTPException, status
from .models import CreateInvoiceRequest, InvoiceResponse, InvoiceListResponse
from .service import InvoiceService

router = APIRouter()

def get_service() -> InvoiceService:
    return InvoiceService()

@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    body: CreateInvoiceRequest,
    service: InvoiceService = Depends(get_service),
) -> InvoiceResponse:
    try:
        invoice = await service.create(body)
        return InvoiceResponse.from_domain(invoice)
    except service.DuplicateInvoiceError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/", response_model=InvoiceListResponse)
async def list_invoices(
    limit: int = 50,
    offset: int = 0,
    service: InvoiceService = Depends(get_service),
) -> InvoiceListResponse:
    items, total = await service.list(limit=limit, offset=offset)
    return InvoiceListResponse(items=items, total=total)
```

Rules:
- Use `APIRouter()`, never `FastAPI()`
- Every endpoint has an explicit `response_model`
- Domain exceptions are caught here and converted to `HTTPException`
- Service is injected via `Depends()`, never instantiated inline
- No business logic — no database queries, no data transformations, no conditionals beyond error mapping

### `service.py` — Pure Business Logic

The service layer contains all domain logic. **Zero framework imports.**

```python
from __future__ import annotations
from uuid import UUID
from .models import CreateInvoiceRequest, Invoice
from .config import InvoiceConfig

class InvoiceError(Exception):
    """Base error for invoice domain."""

class DuplicateInvoiceError(InvoiceError):
    def __init__(self, invoice_number: str):
        self.invoice_number = invoice_number
        super().__init__(f"Invoice {invoice_number} already exists")

class InvoiceService:
    DuplicateInvoiceError = DuplicateInvoiceError

    def __init__(self) -> None:
        self.config = InvoiceConfig()

    async def create(self, request: CreateInvoiceRequest) -> Invoice:
        existing = await self._find_by_number(request.invoice_number)
        if existing:
            raise DuplicateInvoiceError(request.invoice_number)
        # ... creation logic
        return invoice

    async def get(self, invoice_id: UUID) -> Invoice | None:
        # ... lookup logic
        ...

    async def list(self, *, limit: int = 50, offset: int = 0) -> tuple[list[Invoice], int]:
        # ... list logic
        ...
```

Rules:
- **No imports from `fastapi`, `starlette`, or any HTTP framework.** This is the most important rule. If `service.py` imports `Request`, `Depends`, `HTTPException`, or anything HTTP-related, the module is not extractable.
- Define domain exceptions as classes in this file (or a separate `exceptions.py` for complex modules)
- Attach exception classes to the service class so routers can reference them as `service.DuplicateInvoiceError`
- Accept and return Pydantic models or standard Python types
- All public methods have full type hints and docstrings
- Use `async def` for any method that touches I/O

### `models.py` — All Pydantic Schemas

Every data shape gets a Pydantic model. Requests, responses, internal DTOs, database row representations.

```python
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field

# --- Request models ---

class CreateInvoiceRequest(BaseModel):
    invoice_number: str = Field(..., min_length=1, max_length=50)
    client_name: str
    line_items: list[LineItem]

class LineItem(BaseModel):
    description: str
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)

# --- Response models ---

class InvoiceResponse(BaseModel):
    id: UUID
    invoice_number: str
    client_name: str
    total: Decimal
    status: str
    created_at: datetime

    @classmethod
    def from_domain(cls, invoice: Invoice) -> InvoiceResponse:
        return cls(**invoice.model_dump())

class InvoiceListResponse(BaseModel):
    items: list[InvoiceResponse]
    total: int

# --- Internal models ---

class Invoice(BaseModel):
    id: UUID
    invoice_number: str
    client_name: str
    total: Decimal
    status: str
    created_at: datetime
```

Rules:
- Separate request models from response models — never reuse the same model for both
- Use `Field()` with constraints (`min_length`, `gt`, `ge`) for validation
- Use `from_domain()` classmethods to convert internal models to response models
- No framework imports here either — just `pydantic`

### `config.py` — Environment-Based Settings

All configuration through pydantic-settings. Never `os.getenv()`.

```python
from pydantic_settings import BaseSettings

class InvoiceConfig(BaseSettings):
    default_currency: str = "USD"
    max_line_items: int = 100
    payment_reminder_days: int = 30
    tax_rate: float = 0.0

    model_config = {
        "env_prefix": "INVOICE_",
        "env_file": ".env",
        "extra": "ignore",
    }
```

Rules:
- Every config class uses `env_prefix` matching the module name in SCREAMING_SNAKE
- Always set `extra = "ignore"` so unrelated env vars don't crash startup
- Always set `env_file = ".env"`
- All fields have defaults — the module must work with zero configuration for local development
- Document non-obvious settings with `Field(description=...)`

### `migrations/` — Idempotent SQL

```sql
-- 001_create_tables.sql

create table if not exists invoices (
    id uuid primary key default gen_random_uuid(),
    invoice_number text not null unique,
    client_name text not null,
    total numeric(12,2) not null default 0,
    status text not null default 'draft',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table invoices enable row level security;

create index if not exists idx_invoices_status on invoices(status);
create index if not exists idx_invoices_created_at on invoices(created_at desc);
```

Rules:
- Numbered sequentially: `001_`, `002_`, etc.
- Use `if not exists` / `if exists` for idempotency
- Every table gets `created_at timestamptz not null default now()`
- Every table gets `enable row level security`
- `uuid` primary keys with `gen_random_uuid()`
- Foreign keys always specify `on delete` behavior
- Add indexes for columns used in WHERE clauses and ORDER BY

---

## Module Isolation Rules

These rules ensure modules don't develop hidden dependencies on each other or on global state.

### 1. No Cross-Module Imports

Modules never import from each other directly. If module A needs data from module B, it calls B's API endpoints or uses an event/message pattern.

```python
# WRONG — tight coupling
from modules.user_management.service import UserService

# RIGHT — call the API or accept data as a parameter
async def enrich_profile(self, user_id: UUID, user_data: UserData) -> Profile:
    ...
```

### 2. No Global Mutable State

Modules don't write to global variables, module-level caches, or shared singletons. Each module owns its own state.

```python
# WRONG — global state
_cache = {}  # module-level mutable dict

class MyService:
    def get(self, key: str) -> str:
        return _cache.get(key)

# RIGHT — instance state
class MyService:
    def __init__(self) -> None:
        self._cache: dict[str, str] = {}
```

### 3. Database Table Ownership

Each module owns its tables. No module writes to another module's tables. Shared data is read through views or API calls.

### 4. Config Scoping

Each module's config class uses a unique `env_prefix`. No two modules read the same environment variable.

---

## The Extraction Test

Before considering a feature "done," mentally run the extraction test:

1. **Can I copy this directory to another project and it works?** If it has imports reaching outside the module directory (except standard library and declared dependencies), it fails.

2. **Can I understand what this module does from `__init__.py` alone?** The `ModuleInfo` should make the module's purpose, version, and API surface immediately clear.

3. **Can I write a `module.toml` for this in 5 minutes?** If the module's dependencies, API surface, and database tables aren't obvious from the code structure, the boundaries are unclear.

4. **Does the service work without FastAPI?** Import `service.py` in a plain Python script. If it fails because of missing framework dependencies, the separation isn't clean.

---

## Tests

Every module includes at minimum a contract test that verifies structural compliance:

```python
# tests/test_contract.py
from invoice_processing import module_info

def test_module_info_complete():
    assert module_info.name == "invoice_processing"
    assert module_info.version
    assert module_info.description
    assert module_info.router is not None
    assert module_info.prefix.startswith("/api/")
    assert len(module_info.tags) > 0

def test_router_has_routes():
    routes = [r.path for r in module_info.router.routes]
    assert "/" in routes  # at minimum a root endpoint

def test_service_has_no_framework_imports():
    import ast, inspect
    from invoice_processing import service
    source = inspect.getsource(service)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("fastapi"), \
                f"service.py imports from fastapi: {node.module}"
            assert not node.module.startswith("starlette"), \
                f"service.py imports from starlette: {node.module}"
```

---

## Quick Reference

| Question | Answer |
|----------|--------|
| Where does business logic go? | `service.py` — never in routes |
| Where do Pydantic models go? | `models.py` — never inline in routes |
| How do I read config? | `config.py` with pydantic-settings — never `os.getenv` |
| Can services import FastAPI? | **No.** Zero framework imports in `service.py`. |
| Can modules import each other? | **No.** Use API calls or pass data as parameters. |
| What goes in `__init__.py`? | `ModuleInfo` export and nothing else. |
| What goes in `router.py`? | Route definitions that call services. No logic. |
| Do I need migrations for every module? | Yes, if it touches a database. Idempotent SQL with RLS. |
| How do I name the directory? | `snake_case`, matching the `name` in `module.toml`. |
| What's the minimum test? | `test_contract.py` verifying `ModuleInfo` and clean separation. |
