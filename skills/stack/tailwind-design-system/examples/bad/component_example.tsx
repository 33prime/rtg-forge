/**
 * BAD Tailwind component example.
 *
 * Problems demonstrated:
 * - Inline styles mixed with Tailwind classes
 * - Hardcoded colors instead of design tokens
 * - Inconsistent spacing (arbitrary values)
 * - String concatenation instead of cn()
 * - No component variants — duplicated class strings
 * - No responsive design
 * - No dark mode consideration
 * - Duplicated styling patterns
 */

interface Invoice {
  id: string;
  customerName: string;
  status: string;
  total: number;
}

// BAD: No cn() utility, no variant system
export function InvoicePage({ invoices }: { invoices: Invoice[] }) {
  return (
    // BAD: Inline styles mixed with Tailwind
    <div className="flex" style={{ padding: "20px", backgroundColor: "#f8f8f8" }}>
      <h1
        // BAD: More inline styles
        style={{ fontSize: "28px", color: "#333", marginBottom: "20px" }}
      >
        Invoices
      </h1>

      {/* BAD: No responsive grid — fixed layout */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px" }}>
        {invoices.map((invoice) => (
          <div
            key={invoice.id}
            // BAD: String concatenation instead of cn()
            // BAD: Hardcoded colors instead of design tokens
            // BAD: Arbitrary spacing values
            className={
              "border rounded-lg p-[18px] " +
              (invoice.status === "paid" ? "border-green-400" : "border-gray-300")
            }
            // BAD: Mixing inline styles with Tailwind
            style={{ backgroundColor: "white", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}
          >
            {/* BAD: Hardcoded colors, inconsistent sizing */}
            <div className="flex justify-between">
              <span style={{ fontWeight: "bold", color: "#1a1a1a", fontSize: "14px" }}>
                {invoice.customerName}
              </span>

              {/* BAD: Duplicated badge styling — no variant system */}
              {invoice.status === "paid" && (
                <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">
                  paid
                </span>
              )}
              {invoice.status === "draft" && (
                <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded-full text-xs">
                  draft
                </span>
              )}
              {invoice.status === "overdue" && (
                <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs">
                  overdue
                </span>
              )}
              {/* BAD: What about "sent" status? Missing case */}
            </div>

            {/* BAD: Arbitrary margin, hardcoded color */}
            <div style={{ marginTop: "12px" }}>
              <span style={{ fontSize: "24px", fontWeight: "600", color: "#111" }}>
                ${invoice.total}
              </span>
            </div>

            {/* BAD: Inconsistent button styling — no shared component */}
            <button
              className="mt-3 w-full bg-blue-600 text-white py-2 rounded"
              style={{ cursor: "pointer" }}
            >
              View
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
