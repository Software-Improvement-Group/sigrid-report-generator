---
description: "Always apply during code review for any changes in sigrid-report-generator."
applyTo: "src/**/*.py"
---

## Repository context

This repository generates Sigrid quality reports (pptx/docx) from Sigrid API data. It supports both standard SIG report
layouts and custom user-provided templates, using a placeholder system to map Sigrid metrics into template fields.

## Architecture enforcement

This repository uses a layered architecture (`context → domain → placeholders → rendering`); see
`docs/architecture.md` for the full explanation. During code review, flag the following layer boundary
violations:

1. **`context/` interpreting data:** Does new code in `context/` parse, reshape, or apply any semantic meaning to API
   responses? → `context/` returns raw JSON only; interpretation belongs in `domain/`.

2. **`domain/` producing display-ready output:** Does new code in `domain/` return formatted strings, star symbols,
   percentage strings, color names, or any value that only makes sense in the context of a report? → That belongs in
   `placeholders/formatting/`.

3. **`domain/` with report-specific logic:** Does new code in `domain/` contain thresholds, conditions, or computed
   properties that are only meaningful because of how a template displays them? → That belongs in
   `placeholders/implementations/`.

4. **`rendering/` with Sigrid knowledge:** Does new code in `rendering/` reference Sigrid data structures, domain
   objects, or call formatting helpers? → `rendering/` should only contain pptx/docx mechanics; it must not know what
   the values mean.

5. **`utils/` with domain knowledge:** Does new code in `utils/` reference Sigrid API response shapes or depend on what
   Sigrid data looks like? → That belongs in `domain/`; `utils/` must be pure and stateless.

6. **`presets/` using internals:** Does a new or changed preset import from anywhere inside `generator/` other than the
   public `ReportGenerator` API? → Presets are thin wrappers and must not depend on generator internals.

Do not flag import order, unused imports, or dependency direction — a separate CI job enforces those, so review comments
on them just create noise.

## Python design quality

Review all changes as an experienced Python developer would. Apply standard design principles — single responsibility,
clear naming, appropriate use of language features — and flag issues that make the code harder to understand, extend, or
maintain, even if it "works."

A few examples to calibrate the level of issue worth flagging (not exhaustive):

- Using an abstract base class where a mixin or `typing.Protocol` would be more appropriate — ABCs imply "you must
  subclass this," which is a strong commitment when the intent is just shared behavior or a structural contract.
- God methods that combine parsing, transformation, and side effects in one body.
- Vague or misleading names (e.g. `process_data`, `handle`, `result`) that force the reader to study the implementation
  to understand intent.
- Reinventing something the standard library or well-established packages already handle well.
- Mutable default arguments, broad `isinstance` checks where polymorphism would be cleaner, or unfrozen data classes
  that should be frozen.

Use your judgment on severity: focus on issues that would trip up the next person who touches this code, not on minor
style preferences.

## Fail early

Silent defaults (`None`, `0`, `[]`, `""`) are fine when the data is genuinely absent — but when they mask a broken
assumption, they push the failure downstream where it is much harder to diagnose. Flag code that returns a neutral
default where "not found" actually indicates a bug.

Concrete things to look for:

- A lookup that returns `0` or `None` when an entity is not found, where "not found" should never happen in normal
  execution. For example: a system name that came from the same API response is then looked up in a second call and
  silently defaults to zero — that is a bug in the caller, not missing data.
- A calculation that silently excludes items from aggregations (weighted averages, sums, distributions) because a
  helper returned a falsy default instead of surfacing the error.
- `except Exception: pass` or `except Exception: return default` blocks that discard error information.
- Conditionals that skip processing when a value is `None`/`0` without logging or raising, making it impossible to
  tell from the output whether data was missing or simply zero.

An example of code that is **fine**: an API endpoint documents that a metric may not exist for a given system, and the
code returns `None` to represent that — the caller then decides how to display the gap. The distinction is whether the
absence is expected by design or a symptom of something going wrong.

## Version bump

Every change requires a version bump in `setup.cfg` using semantic versioning. Flag the PR if the
version is unchanged.