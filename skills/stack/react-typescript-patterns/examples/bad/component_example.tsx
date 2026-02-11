/**
 * BAD React TypeScript component example.
 *
 * Problems demonstrated:
 * - 'any' types everywhere
 * - No Props interfaces
 * - Inline styles mixed with no system
 * - No custom hooks — all logic in one giant component
 * - Inline functions in JSX (new references every render)
 * - useEffect for derived state
 * - No error handling
 * - No loading states
 * - God component doing everything
 */

import { useEffect, useState } from "react";

// No interface for props — using 'any'
export function InvoicePage(props: any) {
  // All state crammed into one component
  const [data, setData] = useState<any>(null); // 'any' type
  const [name, setName] = useState("");
  const [total, setTotal] = useState(0);
  const [fullLabel, setFullLabel] = useState("");

  // BAD: useEffect for derived state — should be useMemo or just computed
  useEffect(() => {
    setFullLabel(`${name} - $${total}`);
  }, [name, total]);

  // BAD: No error handling, no loading state, no cleanup
  useEffect(() => {
    fetch("/api/invoices")
      .then((r) => r.json())
      .then((d) => setData(d));
    // No error handling!
    // No cleanup for cancelled requests!
    // No loading state management!
  }, []);

  // BAD: No type for the parameter
  const doSomething = (item: any) => {
    // Mutating state directly
    data.items.push(item);
    setData(data); // This won't trigger re-render (same reference)
  };

  return (
    // BAD: Inline styles — no design system, inconsistent
    <div style={{ padding: "20px", margin: "10px", backgroundColor: "#fff" }}>
      <h1 style={{ fontSize: "24px", color: "#333", marginBottom: "16px" }}>Invoices</h1>

      {/* BAD: No loading or error states */}
      {data &&
        data.map((item: any, i: number) => (
          // BAD: Using index as key
          <div key={i} style={{ border: "1px solid #ccc", padding: "12px", marginBottom: "8px" }}>
            <span>{item.name}</span>
            <span style={{ color: item.status === "paid" ? "green" : "red" }}>
              {item.status}
            </span>
            {/* BAD: Inline function creates new reference every render */}
            <button onClick={() => doSomething(item)}>Edit</button>
            {/* BAD: Another inline function */}
            <button
              onClick={() => {
                // Business logic inline in JSX!
                if (window.confirm("Delete?")) {
                  fetch(`/api/invoices/${item.id}`, { method: "DELETE" }).then(() => {
                    // Reload the whole page instead of updating state
                    window.location.reload();
                  });
                }
              }}
              style={{ color: "red", marginLeft: "8px" }}
            >
              Delete
            </button>
          </div>
        ))}

      {/* BAD: Form handling inline with no validation */}
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="name"
        style={{ border: "1px solid #999", padding: "4px" }}
      />
      <input
        value={total}
        // BAD: No type conversion, string to number issues
        onChange={(e: any) => setTotal(e.target.value)}
        placeholder="total"
      />
      <button
        onClick={() => {
          // Inline submission logic
          fetch("/api/invoices", {
            method: "POST",
            body: JSON.stringify({ name, total }),
          });
        }}
      >
        Create
      </button>
    </div>
  );
}
