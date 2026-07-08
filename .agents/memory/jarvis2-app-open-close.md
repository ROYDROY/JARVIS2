---
name: JARVIS2 app open/close duplication
description: jarvis_app.py has two separate, inconsistent implementations for opening/closing apps by voice/text command; know both before touching this logic.
---

`jarvis_app.py` has two independent code paths that both try to open/close apps by name, and only one of them runs for typical "abre X" / "cierra X" commands:

1. `_interceptar_intencion_os` → `_abrir_app_python` / `_cerrar_app_python` — a regex pre-LLM fast path. Always fires first for simple open/close phrasing and never falls through to path 2. Originally required an exact filename match against `indice.json` entries or `es.exe` (Everything CLI) results, which fails for common apps whose display name differs from the real executable (e.g. user says "word", real exe is `WINWORD.EXE`).
2. `ejecutar_con_wrapper`'s own `indice.json` + `es.exe` interceptor — LLM-generated path with fuzzier substring matching. Only reached if path 1 doesn't intercept the command at all.

Fix applied: added `ALIAS_APPS_COMUNES` (near top-level constants, alongside `CONFIG_PATH`/`ES_MULTIPLE`) mapping common Spanish/English app names to their real exe/process names, and wired it into both `_abrir_app_python` and `_cerrar_app_python` as an extra search term before giving up.

**Why:** the two paths were built by separate AI coding sessions (Antigravity + Replit) that got merged, and never reconciled — a recurring source of "why doesn't X work" bugs in this file.

**How to apply:** before changing app-open/close behavior in this file, check both paths, and check whether the fast regex intercept path is the one actually running for the command being tested. This is a Windows-only app (es.exe, PowerShell, os.startfile) — cannot be run/tested in the Replit sandbox, only `python3 -m py_compile` for syntax; real testing must happen on the user's Windows PC.

**Known related pitfall:** `_abrir_app_python` computed `nombre_lower = nombre.lower()` *inside* the `try:` block that opens `indice.json`. On a fresh install `indice.json` doesn't exist yet (it's created lazily after a first successful open), so the file-open line raises before `nombre_lower` is ever assigned, and every later use of `nombre_lower` in that function raises `UnboundLocalError: local variable 'nombre_lower' referenced before assignment` — surfacing to the user as a generic "[ERROR CRÍTICO]" for every single "abre X" command. Fixed by moving the assignment above the `try`. When editing functions like this, check that variables used after/outside a `try` aren't first assigned inside it.

**`procesos_activos` type inconsistency (found via architect review):** `_registrar_y_retornar_apertura` (fast-path) stores a process/exe-name string, but `ejecutar_con_wrapper` (LLM/wrapper path) stored the Python literal `True` in the same dict for a "successfully opened" app. `_cerrar_app_python` reads this dict and does `proceso.replace(".exe", "")`, which crashes with `AttributeError` if the value is `True` — reproducible by opening an app via the wrapper path then closing it via the fast path. Fixed by making the wrapper store a real basename string instead of `True`, plus a defensive type-check in `_cerrar_app_python` treating any non-string legacy value as "not found" rather than crashing.

**Standing architectural debt (not yet fixed, flagged for a future staged cleanup):** an architect-level review of the full file confirmed the two app-open/close engines (see above) are genuine merge duplication, not just messy style, and that ~56 `except Exception` blocks (many bare `pass`) routinely mask real bugs like the ones above — expect more of these to surface as bugs are reported one at a time. Recommendation from that review: don't rewrite the whole 2843-line file; instead unify app control into one code path and replace silent excepts with logged fallbacks, done incrementally as issues surface.
