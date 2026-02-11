# React TypeScript Patterns

Patterns for building type-safe, maintainable React applications with TypeScript. Components should be small, well-typed, and composable.

---

## Component Typing

Every component MUST have an explicit Props interface. Never use `any` or inline object types.

```tsx
// YES — Explicit interface, well-documented
interface InvoiceCardProps {
  invoice: Invoice;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  isSelected?: boolean;
}

function InvoiceCard({ invoice, onEdit, onDelete, isSelected = false }: InvoiceCardProps) {
  return (/* ... */);
}

// NO — Inline types, any, or no types
function InvoiceCard({ invoice, onEdit, onDelete, isSelected }: any) {
  return (/* ... */);
}
```

### Props Rules

1. Props interface is named `<ComponentName>Props`
2. Required props have no `?` modifier
3. Optional props have `?` with a sensible default in destructuring
4. Callback props are typed with explicit parameter and return types
5. Never spread `...rest` without typing — use `ComponentPropsWithoutRef<"div">` if needed

---

## Children Patterns

Use the correct children typing for the component's purpose:

```tsx
// Accepting any React children
interface CardProps {
  children: React.ReactNode;
  variant?: "default" | "outlined";
}

// Render prop pattern — children is a function
interface DataLoaderProps<T> {
  query: () => Promise<T>;
  children: (data: T) => React.ReactNode;
}

// Slot pattern — named children
interface LayoutProps {
  sidebar: React.ReactNode;
  header: React.ReactNode;
  children: React.ReactNode;
}
```

### When to Use Each

| Pattern | Use When |
|---|---|
| `React.ReactNode` | Component wraps generic content |
| `(data: T) => ReactNode` | Component provides data/state to children |
| Named slots | Layout components with multiple content areas |
| No children | Leaf components that render their own content |

---

## Custom Hooks

Extract reusable logic into custom hooks. Hooks encapsulate state, effects, and derived data.

```tsx
// Custom hook for invoice operations
function useInvoice(invoiceId: string) {
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchInvoice() {
      try {
        setIsLoading(true);
        const data = await invoiceApi.getById(invoiceId);
        if (!cancelled) {
          setInvoice(data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error("Unknown error"));
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    fetchInvoice();
    return () => { cancelled = true; };
  }, [invoiceId]);

  return { invoice, isLoading, error } as const;
}
```

### Hook Rules

1. Prefix with `use` — `useInvoice`, `useAuth`, `useDebounce`
2. Return typed objects or tuples with `as const`
3. Handle cleanup in `useEffect` return functions
4. Extract hooks into separate files: `hooks/useInvoice.ts`
5. Keep hooks focused — one concern per hook

---

## Component Composition

Prefer composition over configuration. Build complex UIs from small, focused components.

```tsx
// YES — Composed from small, focused components
function InvoicePage() {
  const { invoices, isLoading } = useInvoices();

  if (isLoading) return <LoadingSpinner />;

  return (
    <PageLayout>
      <PageHeader title="Invoices" action={<CreateInvoiceButton />} />
      <InvoiceFilters />
      <InvoiceList invoices={invoices} />
    </PageLayout>
  );
}

// NO — Monolithic component doing everything
function InvoicePage() {
  // 200 lines of state, effects, handlers, and JSX...
}
```

### Composition Rules

1. Each component does ONE thing
2. Container components handle data/state; presentational components handle display
3. Extract repeated patterns into shared components
4. Use composition instead of prop drilling (Context or component composition)

---

## Generic Components

Use TypeScript generics for reusable components:

```tsx
interface SelectProps<T> {
  options: T[];
  value: T | null;
  onChange: (value: T) => void;
  getLabel: (item: T) => string;
  getKey: (item: T) => string;
  placeholder?: string;
}

function Select<T>({ options, value, onChange, getLabel, getKey, placeholder }: SelectProps<T>) {
  return (
    <select
      value={value ? getKey(value) : ""}
      onChange={(e) => {
        const selected = options.find((opt) => getKey(opt) === e.target.value);
        if (selected) onChange(selected);
      }}
    >
      {placeholder && <option value="">{placeholder}</option>}
      {options.map((opt) => (
        <option key={getKey(opt)} value={getKey(opt)}>
          {getLabel(opt)}
        </option>
      ))}
    </select>
  );
}

// Usage is fully typed:
<Select
  options={customers}
  value={selectedCustomer}
  onChange={setSelectedCustomer}
  getLabel={(c) => c.name}       // TypeScript knows c is Customer
  getKey={(c) => c.id}
  placeholder="Select a customer"
/>
```

---

## Error Boundaries

Wrap async/fallible components with error boundaries:

```tsx
import { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  fallback: ReactNode | ((error: Error) => ReactNode);
  children: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  error: Error | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.props.onError?.(error, errorInfo);
  }

  render() {
    if (this.state.error) {
      const { fallback } = this.props;
      return typeof fallback === "function" ? fallback(this.state.error) : fallback;
    }
    return this.props.children;
  }
}
```

### Error Boundary Rules

1. Wrap each route/page in an error boundary
2. Wrap any component that does data fetching
3. Provide meaningful fallback UIs (not just "Something went wrong")
4. Log errors to your monitoring service in `onError`

---

## Event Handler Typing

Type event handlers explicitly:

```tsx
// Typed handler function
const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault();
  // ...
};

// Typed callback props
interface FormProps {
  onSubmit: (data: FormData) => void;          // Domain event
  onCancel: () => void;                         // Simple action
  onChange: (field: string, value: string) => void;  // Field change
}
```

---

## Avoid Common Anti-Patterns

```tsx
// BAD — Object literal in JSX creates new reference every render
<UserList style={{ marginTop: 16 }} config={{ showAvatar: true }} />

// GOOD — Stable references
const listStyle = { marginTop: 16 } as const;
const listConfig = { showAvatar: true } as const;
<UserList style={listStyle} config={listConfig} />

// BAD — Inline function creates new reference every render
<Button onClick={() => handleDelete(item.id)} />

// GOOD — useCallback for stable reference (when needed for memo'd children)
const handleDeleteItem = useCallback(() => handleDelete(item.id), [item.id]);
<Button onClick={handleDeleteItem} />

// BAD — useEffect for derived state
useEffect(() => {
  setFullName(`${firstName} ${lastName}`);
}, [firstName, lastName]);

// GOOD — useMemo for derived values
const fullName = useMemo(() => `${firstName} ${lastName}`, [firstName, lastName]);
// Or even simpler — just compute it:
const fullName = `${firstName} ${lastName}`;
```
