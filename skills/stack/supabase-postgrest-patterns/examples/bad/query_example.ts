/**
 * BAD Supabase PostgREST query example.
 *
 * Problems demonstrated:
 * - N+1 queries (fetching related data in loops)
 * - No error handling (ignoring .error)
 * - select('*') fetching all columns
 * - No pagination
 * - No TypeScript types
 * - Untyped Supabase client
 */

import { createClient } from "@supabase/supabase-js";

// BAD: No Database type parameter — untyped client
const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!,
);

// BAD: No error handling, select('*'), no pagination, returns 'any'
async function getInvoices(tenantId: string) {
  // BAD: select('*') fetches ALL columns including large JSONB
  const { data } = await supabase
    .from("invoices")
    .select("*")
    .eq("tenant_id", tenantId);
  // BAD: error is completely ignored!
  // BAD: no pagination — could return thousands of rows

  return data; // BAD: type is 'any'
}

// BAD: N+1 queries — fetching customer for EACH invoice in a loop
async function getInvoicesWithCustomers(tenantId: string) {
  const { data: invoices } = await supabase
    .from("invoices")
    .select("*")
    .eq("tenant_id", tenantId);

  // N+1 PROBLEM: One query per invoice to get the customer
  const results = [];
  for (const invoice of invoices ?? []) {
    const { data: customer } = await supabase
      .from("customers")
      .select("*")
      .eq("id", invoice.customer_id)
      .single();

    // Another N+1: One query per invoice to get line items
    const { data: lineItems } = await supabase
      .from("line_items")
      .select("*")
      .eq("invoice_id", invoice.id);

    results.push({
      ...invoice,
      customer,
      lineItems,
    });
  }

  // If there are 100 invoices, this makes 201 queries instead of 1!
  return results;
}

// BAD: No types, no error handling
async function createInvoice(data: any) {
  // BAD: 'any' type for input
  const result = await supabase.from("invoices").insert(data);
  // BAD: not checking result.error
  // BAD: not selecting the returned id
  return result;
}

// BAD: Raw SQL string concatenation via RPC (if that even worked)
async function searchInvoices(query: string) {
  // BAD: Not using PostgREST filters, constructing queries manually
  const { data } = await supabase
    .from("invoices")
    .select("*")
    // BAD: This doesn't actually search — just fetches everything
    ;

  // BAD: Filtering in JavaScript instead of in the database
  return data?.filter((inv: any) =>
    JSON.stringify(inv).toLowerCase().includes(query.toLowerCase())
  );
}

// BAD: No pagination helper, just raw unbounded queries everywhere
async function getAllLineItems() {
  const { data } = await supabase
    .from("line_items")
    .select("*");
  // Could return millions of rows with no limit!
  return data;
}

export { getInvoices, getInvoicesWithCustomers, createInvoice, searchInvoices, getAllLineItems };
