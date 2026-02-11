# Module Extraction Checklist

## Before Extraction

- [ ] Pattern is used in 3+ places
- [ ] Pattern has stabilized (no major changes in last 2 sprints)
- [ ] Tests exist for all current usage sites
- [ ] All tests pass before starting

## Define Boundaries

- [ ] List all public functions/classes the module will expose
- [ ] Define the module's Protocol/interface
- [ ] Identify all external dependencies
- [ ] Verify no circular dependencies will be created

## Extract

- [ ] Create module directory with `__init__.py`
- [ ] Move code to module, keeping original as thin wrapper
- [ ] Update imports at all usage sites
- [ ] Run tests — all must pass

## Validate

- [ ] Module has its own tests
- [ ] Module has clear documentation (README or docstrings)
- [ ] No internal implementation details are exposed
- [ ] All usage sites use the public interface only
