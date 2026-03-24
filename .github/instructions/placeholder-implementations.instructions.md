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