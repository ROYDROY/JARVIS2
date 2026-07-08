---
name: JARVIS2 fallback personality contradicted the ACTIVAR_MOTOR fix
description: The hardcoded default personality used only when system.md is missing told the user to use magic words to activate JARVIS - contradicted the natural-language action detection fix.
---

## Problem

`jarvis_app.py` loads its main personality/system prompt from `system.md`
(not tracked in this repo — see `jarvis2-branch-divergence.md` — lives only
on the user's local PC). If that file is missing at startup, the code falls
back to a hardcoded `SYSTEM_CHAT` + `SYSTEM_LOCAL` default baked into
`jarvis_app.py` itself.

That hardcoded fallback literally instructed the model to tell the user:
*"Dímelo usando palabras como Abrir, Cerrar o Ejecutar para activar mi
núcleo de ingeniería"* — i.e. exactly the "magic word" behavior that was
fixed elsewhere (Fast-Track `ACTIVAR_MOTOR` handoff + refusal-detection
safety net, see `jarvis2-fasttrack-refusal.md`).

**Why this matters:** a behavior fix applied to one code path (the normal
Fast-Track flow reading the real `system.md`) can be silently undone by a
different, rarely-hit fallback path (missing-file case) that was never
updated to match. This is the same "duplicate/inconsistent path" family of
bug as the app open/close duplication and the 3-layer action-detection
split — always grep for hardcoded default/fallback strings when fixing
user-facing wording or behavior, not just the primary path.

**How to apply:** the fallback `SYSTEM_CHAT`/`SYSTEM_LOCAL` strings (near
where `system.md` is opened at startup) were updated to use the same
`ACTIVAR_MOTOR` keyword handoff instead of demanding specific verbs, and to
warn the model this is a Windows machine (no `wc`/`grep`/`ls`/Unix
commands — a real hallucination seen from qwen2.5-coder generating `wc -l`
on Windows and crashing). Since the user's real `system.md` isn't in this
repo, the same Windows-command guardrail should also be added to their
actual local `system.md` — not just this fallback default.
