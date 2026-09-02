# CLAUDE.md

This file provides guidance to Claude when working with code in this repository.

## Code Principles

Write maintainable code: single responsibility, small focused functions, clear naming, avoid duplication, simple control
flow.

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

This repository generates Sigrid quality reports (pptx/docx) from Sigrid API data, using a placeholder system to map
Sigrid metrics into template fields. Data flows strictly one way: `context → domain → placeholders → rendering`

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
    common.py     Font and run helpers shared by both formats.
    docx.py       The Word path.
    pptx/         The PowerPoint path, one module per concern:
      index/        Where the text is, from one cached traversal per document. Locating a
                    placeholder is a scan over cached records, not a fresh walk.
      find.py       Locating text, charts, tables and shapes.
      write.py      Writing text into paragraphs and tables.
      structure.py  Removing slides, shapes and rows. Every helper here must invalidate the
                    index, or writes through stale records are lost silently.
      shapes.py     Shape fill and size.
      colors.py     The palette, and the rules mapping a rating or ratio onto it.

                pptx/__init__.py re-exports the whole API, so callers keep using
                rendering.pptx.X and need not know which module a helper lives in.

utils/          Pure stateless helpers: constants, enums, star-rating math, time/period
                arithmetic. Must not import from context/, domain/, or placeholders/.

presets/        Named report configurations. Each is a thin wrapper around ReportGenerator
                pointing at a bundled .pptx/.docx template. Never imported by generator/.
```

The import boundaries above are mechanically enforced by `import-linter` (configured in `pyproject.toml`). Run
`lint-imports` to check.

### Common violations

**Layer boundary violations** to watch for across the stack (placeholder-specific violations — domain mediation,
orchestration, error handling — are covered in `placeholders/implementations/CLAUDE.md`):

- `context/` parsing, reshaping, or applying semantic meaning to an API response — it must return raw JSON only.
- `domain/` returning display-ready output (formatted strings, star symbols, percentage strings, color names) — that
  belongs in `placeholders/formatting/`.
- `domain/` containing thresholds or conditions that are only meaningful because of how a template displays them —
  that belongs in `placeholders/implementations/`.
- `rendering/` referencing Sigrid data structures, domain objects, or formatting helpers — it must stay pptx/docx
  mechanics only.
- `utils/` referencing Sigrid API response shapes — it must stay pure and stateless.
- A preset importing from anywhere inside `generator/` other than the public `ReportGenerator` API.

Import order, unused imports, and dependency direction are already enforced by `lint-imports` — no need to flag those
separately.

### Nested guidance

- Adding a placeholder, parameterized placeholders, and other placeholder-implementation conventions are covered in
  `placeholders/implementations/CLAUDE.md`.
- Domain singleton conventions are covered in `domain/CLAUDE.md`.

## Design Quality

### Fail early

Silent defaults (`None`, `0`, `[]`, `""`) are fine when data is genuinely absent — but when they mask a broken
assumption, they push the failure downstream. A lookup that returns `0` or `None` when "not found" should never happen
in normal execution is a bug, not missing data. Prefer raising over silently defaulting when absence indicates a
programming error. Also watch for:

- `except Exception: pass` or `except Exception: return default` blocks that discard error information.
- A calculation that silently excludes items from an aggregation (weighted average, sum, distribution) because a
  helper returned a falsy default instead of surfacing the error.

### Python design

Apply standard design principles — single responsibility, clear naming, appropriate use of language features. Examples of
issues worth fixing:

- ABCs where a `typing.Protocol` would suffice (ABCs force subclassing; protocols are structural).
- God methods combining parsing, transformation, and side effects.
- Vague names (`process_data`, `handle`, `result`) that force reading the implementation.
- Mutable default arguments, broad `isinstance` checks where polymorphism is cleaner.

## Version Bump

Every change to production code requires a version bump in `setup.cfg` (semantic versioning). This only applies to
merges into `main` — commits within a branch or PR do not need to bump the version each time.