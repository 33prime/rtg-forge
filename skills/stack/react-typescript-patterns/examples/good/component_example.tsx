/**
 * Good React TypeScript component example.
 *
 * Demonstrates:
 * - Explicit Props interface with proper typing
 * - Custom hook for data fetching with cleanup
 * - Component composition (small focused components)
 * - Proper event handler typing
 * - Conditional rendering patterns
 * - Generic component usage
 */

import { useCallback, useEffect, useMemo, useState } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Invoice {
  id: string;
  customerName: string;
  status: "draft" | "sent" | "paid" | "overdue";
  total: number;
  createdAt: string;
}

// ---------------------------------------------------------------------------
// Custom hook — encapsulates data fetching logic
// ---------------------------------------------------------------------------

interface UseInvoicesResult {
  invoices: Invoice[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

function useInvoices(tenantId: string): UseInvoicesResult {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchInvoices = useCallback(async () => {
    let cancelled = false;

    try {
      setIsLoading(true);
      const response = await fetch(`/api/tenants/${tenantId}/invoices`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data: Invoice[] = await response.json();
      if (!cancelled) {
        setInvoices(data);
        setError(null);
      }
    } catch (err) {
      if (!cancelled) {
        setError(err instanceof Error ? err : new Error("Failed to fetch invoices"));
      }
    } finally {
      if (!cancelled) {
        setIsLoading(false);
      }
    }

    return () => {
      cancelled = true;
    };
  }, [tenantId]);

  useEffect(() => {
    fetchInvoices();
  }, [fetchInvoices]);

  return { invoices, isLoading, error, refetch: fetchInvoices } as const;
}

// ---------------------------------------------------------------------------
// Presentational components — small, focused, typed
// ---------------------------------------------------------------------------

interface StatusBadgeProps {
  status: Invoice["status"];
}

const STATUS_STYLES: Record<Invoice["status"], string> = {
  draft: "bg-gray-100 text-gray-800",
  sent: "bg-blue-100 text-blue-800",
  paid: "bg-green-100 text-green-800",
  overdue: "bg-red-100 text-red-800",
};

function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span className={`rounded-full px-2 py-1 text-xs font-medium ${STATUS_STYLES[status]}`}>
      {status}
    </span>
  );
}

// ---------------------------------------------------------------------------
// InvoiceCard — typed props, callbacks, composition
// ---------------------------------------------------------------------------

interface InvoiceCardProps {
  invoice: Invoice;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  isSelected?: boolean;
}

function InvoiceCard({ invoice, onEdit, onDelete, isSelected = false }: InvoiceCardProps) {
  const formattedTotal = useMemo(
    () =>
      new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
        invoice.total,
      ),
    [invoice.total],
  );

  const handleEdit = useCallback(() => onEdit(invoice.id), [onEdit, invoice.id]);
  const handleDelete = useCallback(() => onDelete(invoice.id), [onDelete, invoice.id]);

  return (
    <div
      className={`rounded-lg border p-4 ${isSelected ? "border-blue-500 ring-2 ring-blue-200" : "border-gray-200"}`}
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-medium text-gray-900">{invoice.customerName}</h3>
          <p className="text-sm text-gray-500">{formattedTotal}</p>
        </div>
        <StatusBadge status={invoice.status} />
      </div>
      <div className="mt-4 flex gap-2">
        <button
          type="button"
          onClick={handleEdit}
          className="rounded bg-blue-500 px-3 py-1 text-sm text-white hover:bg-blue-600"
        >
          Edit
        </button>
        <button
          type="button"
          onClick={handleDelete}
          className="rounded bg-red-50 px-3 py-1 text-sm text-red-600 hover:bg-red-100"
        >
          Delete
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// InvoiceList — container component using custom hook
// ---------------------------------------------------------------------------

interface InvoiceListPageProps {
  tenantId: string;
}

export function InvoiceListPage({ tenantId }: InvoiceListPageProps) {
  const { invoices, isLoading, error, refetch } = useInvoices(tenantId);

  const handleEdit = useCallback((id: string) => {
    console.log("Edit invoice:", id);
  }, []);

  const handleDelete = useCallback((id: string) => {
    console.log("Delete invoice:", id);
  }, []);

  if (isLoading) {
    return <div className="p-8 text-center text-gray-500">Loading invoices...</div>;
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 p-4 text-red-800">
        <p>Failed to load invoices: {error.message}</p>
        <button type="button" onClick={refetch} className="mt-2 text-sm underline">
          Try again
        </button>
      </div>
    );
  }

  if (invoices.length === 0) {
    return <div className="p-8 text-center text-gray-500">No invoices yet.</div>;
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {invoices.map((invoice) => (
        <InvoiceCard
          key={invoice.id}
          invoice={invoice}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      ))}
    </div>
  );
}
