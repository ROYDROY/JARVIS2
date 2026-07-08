---
name: JARVIS wrapper self-blocking validation order
description: Downstream "hardening" checks in ejecutar_con_wrapper() can block code the wrapper itself just generated, if they run after the wrapper rewrites `code`/`code_lower` without a bypass flag.
---

In `jarvis_app.py`'s `ejecutar_con_wrapper()`, several interceptors resolve a user
request (e.g. "open WhatsApp") and legitimately rewrite `code`/`code_lower` to a
sanctioned command (`Start-Process "<resolved absolute path>"`), then continue
executing further down in the same function.

Any later validation block in that function that scans `code_lower` for "unsafe"
patterns (e.g. raw `Start-Process` + a drive-letter path, meant to stop the LLM
from hardcoding paths itself) will also catch — and reject — the wrapper's own
just-generated substitute code, since it structurally matches the same pattern
it's trying to forbid. This silently defeats the interception: the app gets
found and registered in indice.json, logs look successful, but it never
actually launches because a later check blocks it.

**Why:** Two independent safety/rewrite layers were added at different times
without awareness of each other's output shape. The validation layer had no way
to distinguish "LLM wrote this path directly" from "our own interceptor wrote
this path after resolving it safely."

**How to apply:** Whenever adding a new interceptor that rewrites `code` inside
`ejecutar_con_wrapper()`, set a local flag (e.g. `codigo_reescrito_por_wrapper = True`)
at the same time, and make every downstream "block risky LLM code" check also
require `not codigo_reescrito_por_wrapper`. More generally: any time you have
multiple sequential validation/rewrite passes over the same generated-code
string, audit whether an earlier pass's legitimate output can trip a later
pass's guardrail — pattern-matching guardrails can't tell provenance apart
without an explicit flag.

Related: also added a pre-execution guard for Python code containing `input(`
— JARVIS runs generated code non-interactively (subprocess, no real stdin), so
`input()` hangs until timeout and surfaces as a generic
"No he podido ejecutar esa orden correctamente" failure indistinguishable from
a real bug, feeding the "Bucle detectado" loop-abort counter. Detect `input(`
(and rely on the existing reduced timeout for `Read-Host`/`pause` in
PowerShell) and fail fast with an explicit message instead of waiting out the
timeout.
