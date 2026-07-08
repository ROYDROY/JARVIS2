---
name: JARVIS2 Fast-Track inventing factual data (prices/quotes)
description: The local Fast-Track chat model (llama3.1:8b) would confidently state a fabricated price/figure when it had no real injected search data for that specific turn.
---

## Problem

In a live chat log, after a few back-and-forth turns about "el precio del
Bitcoin en euros", a later short follow-up ("búscalo otra vez") did not
match any pattern in `keywords_busqueda` (no "precio en internet" etc.), so
the DuckDuckGo search block was skipped entirely for that turn. The
Fast-Track model (llama3.1:8b) then answered anyway with a confident,
completely made-up number ("El precio del Bitcoin en euros es de
aproximadamente 23.500 euros") with no real data behind it.

**Why:** nothing in the Fast-Track system prompt told the model it was
forbidden to answer factual/volatile questions (price, weather, news,
scores, dates) from its own "memory" when no live `[RESULTADOS
ACTUALIZADOS DE INTERNET...]` block was present in that turn's messages.
Small local models will happily hallucinate a plausible-looking number
instead of admitting they don't know.

**How to apply:** the Fast-Track system prompt (in the `BYPASS CHARLA
RÁPIDA` block of `jarvis_app.py`) now has an explicit "REGLA ANTI-INVENTOS"
telling the model it may only state a concrete/volatile figure if it
literally appears in an injected `[RESULTADOS ACTUALIZADOS DE INTERNET...]`
or `[MEMORIA A LARGO PLAZO...]` block in the *current* turn; otherwise it
must say `ACTIVAR_MOTOR` (to trigger a fresh search) or honestly admit it
doesn't have the current data. If more hallucination cases like this show
up for other data types, the same pattern (name the trusted block, forbid
answering without it) is the fix to reach for.

## Related: "sticky" wrong-action hallucination in the ReAct engine

Same log showed the ReAct engine (qwen2.5-coder:14b), when asked the vague
"búscalo tú" (referring to the bitcoin price), instead ran
`powershell_run es.exe "youtube"` — an unrelated, nonsensical action. A
later turn repeated this same "youtube file search" theme unprompted. This
looks like the small local model latching onto an arbitrary hallucinated
sub-task and having it "stick" across turns via the conversation history,
rather than a context-passing bug (history is confirmed correctly passed;
see jarvis2-search-misrouting.md). No robust code-level fix identified yet
— documented as a known small local-model reliability limitation. If it
recurs, the practical workaround is starting a fresh conversation instead
of continuing one that has already gone off-track.
