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
