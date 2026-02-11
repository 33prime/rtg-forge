# Code Review Checklist

## Correctness

- [ ] Does the code do what the PR description says?
- [ ] Are edge cases handled (empty lists, null values, concurrent access)?
- [ ] Are error paths handled (network failures, invalid input)?
- [ ] No SQL injection, XSS, or other security issues?

## Design

- [ ] Does the change follow existing patterns in the codebase?
- [ ] Are new abstractions justified (not premature)?
- [ ] No circular dependencies introduced?
- [ ] Single responsibility: each function/class does one thing?

## Testing

- [ ] Are there tests for the happy path?
- [ ] Are there tests for error cases?
- [ ] Do existing tests still pass?
- [ ] Is test coverage adequate for the change?

## Data & Migrations

- [ ] Are database migrations reversible?
- [ ] Are indexes added for new query patterns?
- [ ] Is RLS enabled on new tables?
- [ ] Are default values sensible?

## Operations

- [ ] Will this change require environment variable updates?
- [ ] Is the change backward compatible?
- [ ] Are there any performance concerns at scale?
