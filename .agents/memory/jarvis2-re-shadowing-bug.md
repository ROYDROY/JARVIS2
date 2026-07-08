---
name: JARVIS2 local "import X" shadowing bug pattern
description: Recurring UnboundLocalError pattern in jarvis_app.py where a local "import re" inside a method shadows the module-level import; a prior AI agent (Antigravity) claimed to have fixed this but it recurred elsewhere in the same file.
---

## The bug pattern
In Python, if `import X` (or any assignment to `X`) appears ANYWHERE in a function body, `X` becomes a local name for the ENTIRE function — including lines before the import statement executes, and including code paths where that import line is never reached (e.g. inside an `if` branch that doesn't run). Any use of `X` before/without hitting the local import raises `UnboundLocalError: cannot access local variable 'X' where it is not associated with a value`.

`jarvis_app.py` imports `re` at module level (line ~7), which is enough — local `import re` statements inside methods are redundant and dangerous if that same method also uses `re.search`/`re.sub` in a branch that doesn't (or doesn't yet) execute the local import line.

## Why this matters here
This exact bug class caused two separate real incidents in this codebase:
1. `nombre_lower = nombre.lower()` computed inside a `try` block that could fail before assignment.
2. `ejecutar_con_wrapper()` had a local `import re` deep inside an `if is_es_search:` branch, but used `re.search()` earlier in the function (outside that branch) and also in later unrelated branches (Start-Process hardening check, Stop-Process interceptor) that don't depend on `is_es_search`. Any call path that skipped the `is_es_search` branch still crashed with `UnboundLocalError: cannot access local variable 're'` — this matches the exact error users reported when asking JARVIS to run PowerShell commands (e.g. registry edits to run at startup).

A prior agent (Antigravity) documented "fixing" this exact error class by removing local `import re` from `ejecutar_con_wrapper` at specific line numbers, but the fix was incomplete — a different local `import re` inside the same function (added later or missed) reintroduced the identical crash. The bug persisted across multiple "cleanup" rounds because line-number-based fixes don't survive file edits/merges.

**Why:** whack-a-mole patching by line number is unreliable in a file that keeps getting merged/edited by multiple agents (Antigravity + Replit). A "fixed" changelog entry does not guarantee the bug is gone — verify by reading the current code, not by trusting a past summary.

**How to apply:** Before trusting any past "this bug was fixed" claim in this codebase, grep the current file yourself (`import re` at the top of a function body is a red flag) rather than assuming the changelog is still accurate. When adding new code to `jarvis_app.py`, never write `import re` (or `import json`, `import os`, etc.) inside a method — those are already imported at module level; a local import only makes sense for genuinely optional/rarely-used modules not imported globally.
