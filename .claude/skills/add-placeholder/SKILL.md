---
name: add-placeholder
description: "Step-by-step checklist for adding a new placeholder (template key) to the report generator.\n- Use this skill when the user asks to add a new placeholder, template field, or parameterized placeholder (e.g. TECH_1, TECH_2) to a pptx/docx report.\n- When not to use: for editing an existing placeholder's logic, for domain/context/rendering changes unrelated to registering a new template key, or for non-placeholder tasks."
argument-hint: placeholder name and short description of what it renders
---

# Adding a placeholder

1. Add a domain object or property in `domain/system/` or `domain/portfolio/` if new data is needed.
2. Create a placeholder in `placeholders/implementations/text/` (or `charts/`, `table/`, `images/`, `misc/`) using the
   `@text_placeholder()` decorator or by subclassing `Placeholder`.
3. Register it in the relevant `implementations/__init__.py` so it is included in the default set.
4. The function/class name becomes the template key (uppercased). The `key` attribute can be set explicitly for custom
   keys.
5. Add a docstring — it is used to auto-generate `docs/placeholder descriptions.md`. After adding, run
   `./generate_placeholder_docs.py` and commit the result. Never hand-edit `docs/placeholder descriptions.md`
   directly — it is generated; fix the source docstring instead. The docstring should describe what the placeholder
   renders (its output), not internal mechanics.

## Parameterized placeholders

Use `@parameterized_text_placeholder(custom_key="KEY_{parameter}", parameters=[...])` when a single logical value
expands to multiple template keys (e.g. `TECH_1`, `TECH_2`, ...).

See `placeholders/implementations/CLAUDE.md` for the separation-of-concerns rules (`value()` contract, domain
layer mandatory, error handling, type hierarchy) that apply while implementing the placeholder itself.
