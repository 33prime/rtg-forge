# Python Clean Architecture

Patterns for writing clean, maintainable, and type-safe Python code. These are foundational rules that apply to every Python file in the codebase.

---

## Type Hints Everywhere

Every public function, method, and class attribute MUST have type hints. No exceptions.

```python
# YES
def calculate_total(items: list[LineItem], tax_rate: Decimal) -> Decimal:
    ...

# NO
def calculate_total(items, tax_rate):
    ...
```

Use `from __future__ import annotations` at the top of every file for modern annotation syntax.

### Specific Typing Rules

- Use `str | None` instead of `Optional[str]`
- Use built-in generics: `list[str]`, `dict[str, int]`, `tuple[int, ...]`
- Use `TypeAlias` for complex types: `UserId: TypeAlias = UUID`
- Use `Protocol` for structural subtyping instead of ABC where possible
- Use `TypeVar` for generic functions, not `Any`
- `Any` is a code smell. If you reach for it, reconsider your design.

---

## Dataclasses and Pydantic Models

Use structured data types instead of raw dictionaries.

```python
# YES — Clear, typed, documented
@dataclass(frozen=True)
class InvoiceLineItem:
    description: str
    quantity: int
    unit_price: Decimal

    @property
    def total(self) -> Decimal:
        return self.unit_price * self.quantity

# NO — Opaque, untyped, fragile
item = {"description": "Widget", "qty": 5, "price": 10.99}
```

### When to Use What

| Type | Use When |
|---|---|
| `@dataclass` | Internal domain objects, value objects, configs |
| `pydantic.BaseModel` | API boundaries, validation, serialization |
| `TypedDict` | Legacy dict interop, JSON schemas |
| `NamedTuple` | Immutable records, database rows |
| Raw `dict` | Never for domain objects. Only for truly dynamic/unknown structures. |

---

## Service Layer Pattern

Business logic lives in service classes or modules, NOT in route handlers, CLI commands, or model methods.

```python
class InvoiceService:
    def __init__(self, repo: InvoiceRepository, notifier: NotificationService) -> None:
        self._repo = repo
        self._notifier = notifier

    async def create_invoice(self, request: CreateInvoiceRequest) -> Invoice:
        invoice = Invoice.from_request(request)
        await self._repo.save(invoice)
        await self._notifier.send_invoice_created(invoice)
        return invoice
```

### Service Rules

1. Services receive dependencies through `__init__` (constructor injection)
2. Services are stateless — no mutable instance variables beyond dependencies
3. Each public method does ONE thing
4. Methods return typed results, never raw dicts
5. Services raise domain exceptions, not HTTP exceptions

---

## Error Hierarchies

Define a clear error hierarchy per domain. Never use bare `Exception` or generic `ValueError` for business errors.

```python
class InvoiceError(Exception):
    """Base error for invoice domain."""

class InvoiceNotFoundError(InvoiceError):
    def __init__(self, invoice_id: UUID) -> None:
        self.invoice_id = invoice_id
        super().__init__(f"Invoice {invoice_id} not found")

class InvoiceAlreadyPaidError(InvoiceError):
    def __init__(self, invoice_id: UUID) -> None:
        self.invoice_id = invoice_id
        super().__init__(f"Invoice {invoice_id} is already paid")
```

### Exception Rules

- **Never** use bare `except:` or `except Exception:`
- Catch specific exceptions only
- Domain exceptions inherit from a domain base class
- Include relevant context (IDs, states) in exception attributes
- Let unexpected exceptions propagate — don't swallow them

---

## Explicit Returns

Every function that returns a value must have an explicit `return` on every code path. Never rely on implicit `None` returns.

```python
# YES
def find_user(user_id: UUID) -> User | None:
    user = self._repo.get(user_id)
    if user is None:
        return None
    return user

# NO — implicit None return
def find_user(user_id):
    user = self._repo.get(user_id)
    if user:
        return user
```

---

## Small Functions

Functions should do one thing. Target 5-20 lines. If a function exceeds 30 lines, it needs to be split.

### Signs a Function Is Too Large

- Multiple levels of nesting (> 2 levels)
- Multiple try/except blocks
- Comments separating "sections" within the function
- More than 4-5 parameters

### Splitting Strategy

Extract logical sections into private helper methods with descriptive names:

```python
# Instead of one 60-line function:
async def process_order(self, order: Order) -> ProcessedOrder:
    validated = self._validate_order(order)
    priced = self._apply_pricing(validated)
    await self._reserve_inventory(priced)
    return await self._finalize_order(priced)
```

---

## Module Organization

```
src/
  domain/
    models.py          # Dataclasses, enums, value objects
    errors.py          # Domain exception hierarchy
    types.py           # Type aliases, protocols
  services/
    invoice_service.py # Business logic
  repositories/
    invoice_repo.py    # Data access
  api/
    routes/            # HTTP handlers (thin)
    dependencies.py    # FastAPI Depends factories
```

### Import Rules

- No circular imports. If you have them, your layering is wrong.
- Domain layer imports nothing from services or API layers.
- Services import from domain, never from API.
- API layer imports from services and domain.

---

## Constants and Configuration

```python
# YES — Named constants
MAX_RETRY_ATTEMPTS = 3
DEFAULT_PAGE_SIZE = 50
INVOICE_DUE_DAYS = 30

# NO — Magic numbers
if retries > 3:
    ...
results = query.limit(50)
```

Use environment variables through a typed settings class (Pydantic `BaseSettings`), never through raw `os.getenv()` scattered across the codebase.
