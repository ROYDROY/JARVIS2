---
name: JARVIS2 repo has diverged local "master" vs Replit "main"
description: Buscador.py, MotorVoz.py, requirements.txt are not in this workspace's git history at all — they exist only in a separate local "master" branch on the user's PC.
---

## Context

The user's local PC repo has (at least) two branches: `master` (the user's
original local history, containing files like `Buscador.py` and
`MotorVoz.py`) and whatever branch this Replit workspace/`main` tracks —
which does NOT contain those files (confirmed via `git log --all` here:
they never appear in this workspace's tracked history, not even in old
commits).

**Why this matters:** if a file referenced by `jarvis_app.py` (via
`import X`) appears "missing" and `git log --all -- path` here shows
nothing, that does not mean the file never existed or must be recreated
from scratch — it may simply live only in the user's local `master` branch,
untouched by this workspace. The user's local Antigravity agent recovered
`Buscador.py` and `MotorVoz.py` this way (`git checkout master -- <file>`)
without needing external backups.

**How to apply:** when a "missing module" error refers to a project-local
file (not a pip package), first ask whether it might exist on another local
branch before assuming it needs to be rewritten or restored from backup.
Also worth flagging to the user at some point: consider merging/aligning
the two branches so this workspace's history isn't missing files the local
PC depends on — otherwise this confusion will resurface.
