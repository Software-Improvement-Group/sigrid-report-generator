# CLAUDE.md

This file provides guidance to AI agents when working with code in this repository.

## Commands

```bash
# Should be installed already with
pip install -e .

# Run with
report-generator --help

# Run all unit tests
pytest

# Lint
ruff check .          # check for violations (add --fix to auto-fix)
ruff format .         # format (add --check to only check)

# Architecture linting (enforces import boundaries)
lint-imports
```

## Architecture

Data flows strictly one way: `context → domain → placeholders → rendering`

```
context/        Raw HTTP calls to Sigrid API. Returns JSON only. Uses @cache to avoid
                redundant calls. Module-level globals hold bearer token, customer, system,
                and period; set via sigrid_api.set_context() before generating.

domain/         Wraps context calls into lazy-loaded, cached domain objects (module-level
  system/       singletons). Computes weighted averages, aggregates, sorts. No strings,
  portfolio/    no star symbols, no colors — purely domain-meaningful values.
  shared/       system/ and portfolio/ must not import each other.

placeholders/   Bridge between domain and the report file.
  implementations/  Defines template keys (e.g. MAINT_RATING). Calls domain for values,
                    applies presentation-level transforms (stars, %, diffs), then calls
                    rendering/ to write to the file.
  formatting/   Presentation helpers: float→stars, ratio→%, diff→"+0.3". No pptx/docx.
  rendering/    pptx/docx file mechanics only. No Sigrid knowledge. Never calls domain.

utils/          Pure stateless helpers: constants, enums, star-rating math, time/period
                arithmetic. Must not import from context/, domain/, or placeholders/.

presets/        Named report configurations. Each is a thin wrapper around ReportGenerator
                pointing at a bundled .pptx/.docx template. Never imported by generator/.
```

The import boundaries above are mechanically enforced by `import-linter` (configured in `pyproject.toml`). Run `lint-imports` to check.

### Adding a placeholder

1. Add a domain object or property in `domain/system/` or `domain/portfolio/` if new data is needed.
2. Create a placeholder in `placeholders/implementations/text/` (or `charts/`, `table/`, `images/`, `misc/`) using the `@text_placeholder()` decorator or by subclassing `Placeholder`.
3. Register it in the relevant `implementations/__init__.py` so it is included in the default set.
4. The function/class name becomes the template key (uppercased). The `key` attribute can be set explicitly for custom keys.
5. Add a docstring — it is used to auto-generate `docs/placeholder descriptions.md`. After adding, run `./generate_placeholder_docs.py` and commit the result.

### Parameterized placeholders

Use `@parameterized_text_placeholder(custom_key="KEY_{parameter}", parameters=[...])` when a single logical value expands to multiple template keys (e.g. `TECH_1`, `TECH_2`, ...).

### Domain singletons

Domain modules expose module-level singleton objects (e.g. `maintainability_data`, `osh_portfolio_data`). These are lazily loaded and cached via `functools.cached_property` or `@cache` on the underlying API calls. Tests that exercise domain logic must patch `sigrid_api` functions or call `sigrid_api.set_context()` / `sigrid_api.reset_context()` to avoid polluting state across tests.

## Code Principles

Write maintainable code: single responsibility, small focused functions, clear naming, avoid duplication, simple control flow.