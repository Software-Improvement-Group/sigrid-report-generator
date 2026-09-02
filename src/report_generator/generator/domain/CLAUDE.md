# Domain

## Domain singletons

Domain modules expose module-level singleton objects (e.g. `maintainability_data`, `osh_portfolio_data`). These are
lazily loaded and cached via `functools.cached_property` or `@cache` on the underlying API calls. Tests that exercise
domain logic must patch `sigrid_api` functions or call `sigrid_api.set_context()` / `sigrid_api.reset_context()` to
avoid polluting state across tests.
