# BAD Module Extraction Approach

## What Goes Wrong

- Extract after first use (too early, pattern hasn't stabilized)
- No tests before extraction (no safety net)
- Copy-paste code instead of moving it (now two copies to maintain)
- No clear public interface (everything is exported)
- Circular dependencies between module and parent
- No documentation (nobody knows how to use the module)
- Extract into a separate repo immediately (premature, adds overhead)
