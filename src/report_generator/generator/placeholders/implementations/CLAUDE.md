# Placeholder Implementations

## Separation of concerns

1. **Data computation** (`value()`): computes the data a placeholder represents (a string, a rating, a figure-data
   dict).
2. **Document rendering** (`resolve_pptx` / `resolve_docx`): takes computed data and writes it into the target document
   format, using shape dimensions, paragraph styles, or other format-specific context.

Flag code that mixes these — e.g. a `value()` method that accepts document dimensions, creates a matplotlib figure at a
specific size, or depends on how/where the result will be rendered.

## `value()` contract

All `value()` signatures must match the contract defined by their base class:

- `Placeholder.value(cls, parameter=None)` — non-parameterized placeholders.
- `ParameterizedPlaceholder.value(cls, parameter)` — parameterized placeholders receive their parameter, nothing else.

No extra arguments (e.g. `additional_parameter`, dimension dicts) beyond what the base class defines. If only one
subclass family needs extra context, handle it in that family's `resolve_*` override.

## Call `value_cb()` once, before the rendering loop

Every call to `value_cb()` re-executes the full data computation pipeline. In every `resolve_pptx` / `resolve_docx`
method, call `value_cb()` **once before** iterating over shapes, charts, paragraphs, or tables. Never invoke it inside a
loop.

## Type hierarchy must match directory

Each typed directory (`text/`, `table/`, `charts/`, `images/`) defines a type boundary — every class in that directory
must be a subtype of the directory's base class (Liskov-consistent). This applies transitively: intermediate abstractions
must also extend the directory base, not just leaf classes.

- A class that only needs the root `Placeholder` interface belongs in `misc/`, not a typed directory.
- Shared behaviour within a directory uses utility functions (composition), not mixins.
- Cross-type reuse belongs in `formatting/` (pure value transforms) or `rendering/` (document-model mechanics).
- Intermediate abstractions and their concrete subclasses must be co-located in the same module.

## Domain layer is mandatory

Placeholders are the view layer — they format, they do not fetch or transform:

- No direct data access — never import from `context/` or call `sigrid_api`.
- No data orchestration — never pass output from one domain object into another domain object's method.
- No data transformation — filtering, aggregating, reshaping dicts, computing averages belong in domain.

Heuristic: if `value()` exceeds ~10 lines, manipulates dict keys from API responses, or calls multiple domain methods to
assemble an intermediate value, domain logic has leaked in.

## Error handling

Do not add try/except. The base class `_call_resolve_method` catches failures centrally and lets report generation
continue.
