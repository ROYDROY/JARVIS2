---
name: JARVIS2 Fast-Track model ignoring ACTIVAR_MOTOR instruction
description: Local chat model sometimes refuses actions in natural language instead of emitting the ACTIVAR_MOTOR handoff keyword; needed a refusal-detection safety net.
---

## Problem

`jarvis_app.py`'s Fast-Track (local Ollama chat) path is instructed via system
prompt to respond with the exact keyword `ACTIVAR_MOTOR` when the user asks
for a system action (open/close apps, diagnostics, file search, etc.), so the
app can silently hand off to the ReAct engine. Small local models (e.g.
llama3.1:8b) do not reliably obey this meta-instruction — instead they often
explain their "limitations" in natural language (e.g. "no tengo acceso al
PC", "usa verbos como Abrir o Ejecutar para activar mi motor"). This surfaces
to the user as JARVIS refusing to act and demanding a specific magic word,
which is exactly the broken UX the user rejected.

**Why:** you cannot fix small-model instruction-following by rewording the
system prompt alone — it will drift again. A code-level safety net is needed
downstream of the model's own output.

**How to apply:** `_parece_rechazo_de_capacidad()` (module-level regex
heuristic, near `determinar_rol`) scans the Fast-Track response text for
refusal/limitation phrasing. If matched, treat it exactly like the model had
said `ACTIVAR_MOTOR` — reroute to the ReAct engine instead of showing the
refusal to the user. When extending this app's action-detection, remember
there are now three independent layers that must stay consistent:
1. `_interceptar_intencion_os()` — fast regex intercept for simple abrir/cerrar, before any LLM call.
2. Fast-Track LLM `ACTIVAR_MOTOR` keyword + `_parece_rechazo_de_capacidad()` refusal fallback — natural-language action detection.
3. The ReAct engine's own `_bypass_seguridad` system-prompt block — forbids the engine itself from refusing once inside.
If you touch one, check whether the other two need the same fix (see also `jarvis2-app-open-close.md` for the general "duplicate paths from the Antigravity+Replit merge" pattern in this file).
