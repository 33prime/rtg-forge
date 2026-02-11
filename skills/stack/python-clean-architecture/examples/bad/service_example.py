"""BAD EXAMPLE — Same invoice logic but violating clean architecture patterns.

Problems demonstrated:
- No type hints
- Bare exceptions
- God function doing everything
- Raw dicts instead of dataclasses
- Magic numbers
- Implicit None returns
- No error hierarchy
- Mutable default argument
"""

import os
import json

# No domain models — just raw dicts everywhere

def process_invoice(data, db=None, items=[]):  # Mutable default argument!
    """Do everything invoice-related in one massive function."""
    try:
        # No validation, no types
        invoice = {
            "customer": data.get("customer"),
            "items": items or data.get("items", []),
            "status": "draft",
        }

        # Magic number, no constant
        if len(invoice["items"]) > 100:
            return None  # Implicit failure — caller has no idea why

        total = 0
        for item in invoice["items"]:
            # No validation, no types, dict access everywhere
            qty = item.get("qty", 0)
            price = item.get("price", 0)
            # Using float for money — precision errors
            total += qty * price

        invoice["total"] = total

        # Bare exception swallowing errors
        try:
            if db:
                db.execute(
                    "INSERT INTO invoices VALUES (%s, %s)",
                    (json.dumps(invoice), total),
                )
        except:  # noqa: E722 — bare except!
            pass  # Silently swallows ALL errors including KeyboardInterrupt

        # Inline notification logic in the service
        try:
            import smtplib
            server = smtplib.SMTP(os.getenv("SMTP_HOST"))  # Raw os.getenv
            server.sendmail(
                "noreply@example.com",
                data.get("email"),  # Could be None
                f"Invoice created for ${total}",
            )
        except Exception:
            print("email failed")  # print instead of logging

        # Sometimes returns dict, sometimes None, no explicit contract
        if data.get("return_invoice"):
            return invoice
        # Implicit None return — caller doesn't know if this succeeded
    except Exception as e:
        # Catches everything, logs nothing useful
        print(f"error: {e}")
        return None


def get_invoice(id):
    """Get an invoice — no types, no error handling."""
    # Hardcoded connection string in code
    import psycopg2
    conn = psycopg2.connect("postgresql://user:pass@localhost/db")
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM invoices WHERE id = {id}")  # SQL injection!
    row = cur.fetchone()
    if row:
        return {"id": row[0], "data": row[1]}
    # Implicit None return — no InvoiceNotFoundError


def mark_paid(id):
    """Mark invoice as paid — no checks, no types."""
    import psycopg2
    conn = psycopg2.connect("postgresql://user:pass@localhost/db")
    cur = conn.cursor()
    # No check if already paid, no status validation
    cur.execute(f"UPDATE invoices SET status = 'paid' WHERE id = {id}")  # SQL injection
    conn.commit()
    return True  # Always returns True even if no rows updated
