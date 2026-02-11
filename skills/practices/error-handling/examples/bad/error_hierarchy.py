"""BAD error handling — bare excepts, swallowed errors, no hierarchy."""


def get_invoice(invoice_id):
    try:
        result = db.query(f"SELECT * FROM invoices WHERE id = {invoice_id}")
        return result
    except:  # Bare except — catches KeyboardInterrupt, SystemExit, everything
        pass  # Silently swallows the error
        # Caller has no idea this failed


def process_payment(data):
    try:
        # ... payment logic ...
        pass
    except Exception as e:
        print(f"Error: {e}")  # Logs but still swallows — caller thinks it succeeded
        return None  # Implicit failure via None return
