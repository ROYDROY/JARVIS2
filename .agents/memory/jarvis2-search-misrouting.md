---
name: JARVIS2 web-search queries misrouted to the code engine
description: determinar_rol's keyword-based classifier put simple "search the web" questions into the Ingeniero (coder) role, causing the model to write a non-executing tutorial instead of answering with fetched results.
---

## Problem

`determinar_rol()`'s `keywords_codigo` list includes `"busca"`/`"encuentra"` so
that requests like "busca el archivo X y ábrelo" get routed to the
Ingeniero/ReAct (qwen2.5-coder) engine. But this same keyword match also
fired for plain informational queries like "busca en internet el precio del
bitcoin en euros" — even though the separate Buscador (DuckDuckGo) block
already fetches the answer and injects it into the prompt as plain text.

Routing that case to the coder model was wrong: qwen2.5-coder responded with
a "here's how you could look this up yourself" tutorial instead of just
reporting the fetched price, and falsely claimed `[TAREA_COMPLETADA]`
without answering the user's question at all.

**Why:** the coder/ReAct role is tuned to emit code blocks and treat the
turn as an engineering task. Once Buscador.py has already fetched the
answer, there is nothing left to execute — it's a pure Q&A turn and should
go through the conversational Fast-Track model instead.

**How to apply (FIX #8):** after a successful Buscador web search (results
found and injected into `prompt_final`), the app now force-routes to
`MODEL_CHAT` (Fast-Track) instead of calling `seleccionar_cerebro()`,
unless the user explicitly selected Ingeniero mode or `forzar_local` is set
(e.g. an attached image/file). If you add more "keyword implies coder role"
entries to `determinar_rol`, check whether they can also match a plain
informational request answered by a side-channel data fetch (web search,
RAG memory, etc.) — those should still get a conversational answer, not a
code-execution turn.

## Related but NOT a code bug: vague follow-up ("Hazlo tú") hallucination

Separately, when the user's follow-up was the vague "Hazlo tú" ("You do
it"), referring back to "search the bitcoin price", the ReAct engine
(qwen2.5-coder:14b) ignored that context entirely and hallucinated an
unrelated multi-step "system diagnostics / read files" tutorial instead.
This was confirmed NOT a context-passing bug — the last 10 messages of
`interpreter.messages` (including the bitcoin question and JARVIS's prior
reply) are correctly included in the messages sent to the model for every
ReAct step. This looks like a genuine small local-model (14B) weakness at
resolving ambiguous pronoun references ("hazlo", "eso", "lo mismo") rather
than something fixable in `jarvis_app.py`. If this recurs, the practical
mitigation is asking the user to be explicit rather than relying on
anaphora ("busca tú el precio del bitcoin" instead of "hazlo tú").
