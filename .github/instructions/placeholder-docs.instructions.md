---
description: "Apply when reviewing changes to the generated placeholder descriptions documentation."
applyTo: "docs/placeholder descriptions.md"
---

## This file is auto-generated

`docs/placeholder descriptions.md` is generated from the pydoc (docstring) of each placeholder function or class
by running `./generate_placeholder_docs.py`.

When reviewing changes to this file:

1. Do not suggest edits to the generated markdown directly — flag the source docstring in the placeholder
   implementation instead.
2. Verify the docstring accurately describes what the placeholder renders (its output), not internal mechanics.
3. If a placeholder lacks a docstring, flag it — every placeholder must have one since it drives this documentation.
