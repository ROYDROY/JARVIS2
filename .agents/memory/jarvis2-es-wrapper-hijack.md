---
name: JARVIS2 "es" wrapper hijacking real code execution
description: A too-broad regex in ejecutar_con_wrapper treated the common Spanish word "es" as an invocation of the es.exe (voidtools Everything) search tool, silently hijacking unrelated PowerShell code before it could run.
---

## Problem (root cause, not a symptom)

`ejecutar_con_wrapper()` intercepts non-Python code blocks that look like
they're trying to invoke `es.exe` (the voidtools "Everything" search CLI
placed at `herramientas/es.exe`), so JARVIS can fast-path app launches via
`indice.json` instead of letting the LLM fumble around. The detection used
to be:

```python
if "es.exe" in code_lower or re.search(r'\b(?:es\.exe|es)\s+', code_lower):
    is_es_search = True
```

`es` is the single most common word in Spanish (verb "ser", 3rd person: "is").
Any non-Python code block containing an ordinary Spanish comment or string
like `# Esto es una prueba` or `Write-Output "El resultado es correcto"`
matched `\bes\s+` and got redirected into the es.exe search flow — the
LLM's actual (correct) code was silently discarded and replaced with a
file-search attempt for whatever token happened to follow "es". This is a
strong root-cause candidate for many of the session's "Bucle detectado",
empty/nonsensical responses, and bizarre unrelated actions (e.g. an
`es.exe "youtube"` search appearing out of nowhere) — the LLM's real code
was never given a chance to execute.

**Confirmed via a live debug log** showing `[WRAPPER] 'buscador.py' no
está en indice.json. Buscando en el sistema con es.exe...` when the model
was trying to run `Buscador.py`, and a second interception of
`Buscar-Archivo.ps1 -Nombre "es.exe"`.

**How to apply (FIX #10):** detection is now restricted to (a) the literal
substring `es.exe` anywhere in the code, or (b) a line whose FIRST token
(after stripping whitespace, skipping comment lines) is exactly `es`,
`.\es`, `./es`, `&es`, or `&"es"` — i.e. only when `es` is actually being
invoked as a command, never when it's just a word inside a sentence or
comment. If you touch this interceptor again, always test against a
Spanish-language comment containing "es" to make sure it doesn't
re-trigger a false positive — this is the single highest-risk regex in the
file given the app's language.

## Related, separate but compounding issue: es.exe binary may be missing

The same debug log showed `[WRAPPER ERROR] Error en flujo es.exe: [WinError
2] El sistema no puede encontrar el archivo especificado` for BOTH
interception attempts — i.e. `herramientas/es.exe` itself does not exist
on disk. This is an environment/setup issue on the user's PC, not
something fixable from this repo: they need to download the voidtools
"Everything" command-line tool (`es.exe`) and place it at
`JARVIS\herramientas\es.exe`. Without it, ALL non-indexed app searches and
launches silently fail (previously with a cryptic WinError2, now caught
explicitly with a clearer `[WRAPPER ERROR]` message telling the user to
install it).
