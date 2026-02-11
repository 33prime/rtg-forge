# Parallel Execution

> This skill is under development.

Workflow patterns for running independent tasks in parallel to improve performance and throughput.

## Topics to Cover

- Identifying independent tasks suitable for parallel execution
- `asyncio.gather()` with `return_exceptions=True`
- `asyncio.TaskGroup` for structured concurrency (Python 3.11+)
- Semaphores for bounded concurrency
- `Promise.all()` and `Promise.allSettled()` in TypeScript
- Handling partial failures (some tasks succeed, some fail)
- Progress tracking for parallel task batches
- Avoiding thundering herd on shared resources
