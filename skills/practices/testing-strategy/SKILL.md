# Testing Strategy

> This skill is under development.

Patterns for building reliable test suites across Python and TypeScript codebases.

## Topics to Cover

- Test pyramid: unit > integration > e2e ratio
- Pytest patterns: fixtures, parametrize, conftest organization
- Vitest patterns: component testing, MSW for API mocking
- Contract tests at service boundaries
- Fixture factories (factory_boy, faker)
- Mocking strategy: mock at boundaries, not internals
- Database testing: transactions, seeding, isolation
- CI integration: parallel tests, coverage thresholds
- Testing async code properly
