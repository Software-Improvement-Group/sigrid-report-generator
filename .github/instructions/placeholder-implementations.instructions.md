---
description: "Apply when reviewing, creating, or refactoring placeholder implementations and their base classes."
applyTo: "src/report_generator/generator/placeholders/implementations/**/*.py"
---

## Placeholder architecture

The placeholder system resolves template keys into values and renders them into documents. There are two distinct
responsibilities that must stay separate:

1. **Data computation** (`value()`): computes the data a placeholder represents (a string, a rating, a figure-data
   dict).
2. **Document rendering** (`resolve_pptx` / `resolve_docx`): takes computed data and writes it into the target document
   format, using shape dimensions, paragraph styles, or other format-specific context.

Flag code that mixes these two concerns — for example a `value()` method that accepts document dimensions, creates a
matplotlib figure at a specific size, or otherwise depends on how or where the result will be rendered. The rendering
step belongs in the `resolve_*` method, which has access to the target shape.

## Keep the `value()` contract consistent

All `value()` signatures must match the contract defined by their base class:

- `Placeholder.value(cls, parameter=None)` — non-parameterized placeholders.
- `ParameterizedPlaceholder.value(cls, parameter)` — parameterized placeholders receive their parameter, nothing else.

Flag any `value()` method that adds extra arguments (e.g. `additional_parameter`, `optional_parameter`, dimension dicts)
beyond what the base class defines. If only one subclass family needs extra context, that context should be handled in
that family's `resolve_*` override — not threaded through the shared `value()` interface.

## Don't pollute shared interfaces for one implementation's needs

If a new parameter or callback argument is added to a base class or shared call chain, check whether **all** subclasses
actually use it. A parameter that only one subclass family needs should not appear in the shared interface — it should
be handled via a method override in that specific family. Watch for:

- Base class methods gaining parameters that most subclasses ignore or default to `None`.
- Callback wrappers forwarding "mystery" arguments that only one caller provides.
- `= None` default arguments added purely to avoid `TypeError` in callers that don't use the parameter.

## Call `value_cb()` once, before the rendering loop

Every call to `value_cb()` re-executes the full data computation pipeline — API calls, portfolio aggregation, color
mapping, and anything else in `value()`. Repeating this per shape is a silent performance bug that scales with the
number of placeholder occurrences in the template.

In every `resolve_pptx` / `resolve_docx` method, call `value_cb()` (or `value_fn()`) **once before** iterating over
shapes, charts, paragraphs, or tables. The computed value does not depend on individual element dimensions or
positions — only the subsequent draw/render step does.

Flag any `resolve_*` method where `value_cb()` or `value_fn()` is invoked inside a shape/chart/paragraph/table loop.

## Domain layer is mandatory

Placeholders are the view layer — they format, they do not fetch or transform:

1. **No direct data access.** Never import from `context/` or call `sigrid_api`. All data arrives via domain objects.
2. **No data orchestration.** Never pass output from one domain object into another domain object's method — that
   composition belongs as a property on the domain object itself.
3. **No data transformation.** Filtering, aggregating, reshaping dicts, computing averages — all domain work.

Heuristic: if `value()` exceeds ~10 lines, manipulates dict keys from API responses, or calls multiple domain
methods to assemble an intermediate value, domain logic has leaked in.

## Error handling

`_call_resolve_method` in `base.py` already catches failures (`SigridAPIRequestFailedError`, `KeyError`,
`AttributeError`, `ValueError`), logs them, and lets report generation continue. 