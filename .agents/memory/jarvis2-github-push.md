---
name: JARVIS2 GitHub push blocked
description: This Replit workspace's origin remote (github.com/ROYDROY/JARVIS2.git) only allows reads, not pushes.
---

The `origin` remote (`https://github.com/ROYDROY/JARVIS2.git`) is reachable for reads (`git ls-remote`, `fetch` work fine) but pushes are not authenticated: no GitHub connector (`listConnections('github')` returns empty), no `GITHUB_TOKEN`, no git credential helper. `git push` does not fail fast — it hangs waiting on `replit-git-askpass`, which never resolves.

**Why:** Confirmed across multiple sessions/tasks with identical results.

**How to apply:** Before attempting `git push` in this workspace, re-check `listConnections('github')` and env for a token first. If still absent, do not run `git push` (it will hang) — commit locally, explain the blocker, and ask the user to connect GitHub with write access (Replit GitHub integration or a PAT secret).
