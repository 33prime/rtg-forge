# Error Handling

> This skill is under development.

Cross-cutting patterns for handling errors in Python and TypeScript applications. Errors should be explicit, typed, contextual, and never silently swallowed.

## Topics to Cover

- Domain error hierarchies (base class per domain)
- Never swallowing errors — catch specifically or let propagate
- Typed error responses for APIs (consistent error shape)
- Error context: always include relevant IDs and state
- Retry patterns with exponential backoff
- Circuit breaker pattern for external services
- Logging errors with structured context
- Python: custom exceptions with attributes
- TypeScript: discriminated union error types (`Result<T, E>`)
