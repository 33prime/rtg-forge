"""BAD EXAMPLE — FastAPI router violating all patterns.

Problems demonstrated:
- Sync route handlers doing I/O
- No Depends() — manual dependency creation
- No Pydantic models — raw dicts in and out
- Wrong/missing status codes
- Business logic inline in handlers
- No response model specification
- Bare exception handling in routes
"""

from fastapi import APIRouter
import psycopg2
import json
import os

router = APIRouter()

# No prefix, no tags
# No dependency injection — hardcoded DB connection

def get_db():
    # Hardcoded credentials in code!
    return psycopg2.connect("postgresql://user:password@localhost/mydb")


@router.get("/invoices")  # No response_model
def get_invoices():  # Sync! No type hints, no auth
    """Get all invoices."""
    try:
        db = get_db()  # No Depends(), manual connection
        cursor = db.cursor()
        cursor.execute("SELECT * FROM invoices")  # No pagination!
        rows = cursor.fetchall()

        # Building response manually — no Pydantic model
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "data": json.loads(row[1]),
                "total": float(row[2]),  # float for money!
            })
        db.close()
        return result  # Returns 200 with raw list, no wrapper
    except Exception as e:
        # Catching everything, returning 200 with error in body
        return {"error": str(e)}


@router.post("/invoices")  # No status_code=201!
def create_invoice(data: dict):  # raw dict, no Pydantic model
    """Create invoice with all logic inline."""
    try:
        db = get_db()
        cursor = db.cursor()

        # Business logic in the route handler!
        items = data.get("items", [])
        total = 0
        for item in items:
            total += item.get("qty", 0) * item.get("price", 0)

        # No validation at all
        cursor.execute(
            "INSERT INTO invoices (data, total) VALUES (%s, %s) RETURNING id",
            (json.dumps(data), total),
        )
        row = cursor.fetchone()
        db.commit()
        db.close()

        # Sending email inline in the route handler!
        try:
            import smtplib
            server = smtplib.SMTP(os.getenv("SMTP_HOST"))
            server.sendmail("noreply@ex.com", data.get("email"), "Invoice created")
        except:
            pass  # Silently swallow email errors

        return {"id": row[0], "total": total}  # Raw dict response

    except Exception as e:
        print(f"Error: {e}")  # print instead of logging
        return {"error": "something went wrong"}  # 200 status with error!


@router.get("/invoices/{id}")  # No response_model, param not typed
def get_invoice(id):  # No UUID type, no auth
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM invoices WHERE id = {id}")  # SQL INJECTION!
    row = cursor.fetchone()
    db.close()
    if row:
        return {"id": row[0], "data": row[1]}
    return {"error": "not found"}  # Returns 200 with error message instead of 404!


@router.post("/invoices/{id}/pay")  # No status code
def pay_invoice(id):
    db = get_db()
    cursor = db.cursor()
    # No check if already paid
    cursor.execute(f"UPDATE invoices SET status = 'paid' WHERE id = {id}")
    db.commit()
    db.close()
    return {"ok": True}
