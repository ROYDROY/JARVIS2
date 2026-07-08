---
name: JARVIS2 GitHub push blocked
description: This Replit workspace's origin remote (github.com/ROYDROY/JARVIS2.git) only allows reads, not pushes.
---

The `origin` remote (`https://github.com/ROYDROY/JARVIS2.git`) is reachable for reads (`git ls-remote`, `fetch` work fine) but pushes are not authenticated: no GitHub connector (`listConnections('github')` returns empty), no `GITHUB_TOKEN`, no git credential helper. `git push` does not fail fast — it hangs waiting on `replit-git-askpass`, which never resolves.

**Why:** Confirmed across multiple sessions/tasks with identical results.

**How to apply:** Before attempting `git push` in this workspace, re-check `listConnections('github')` and env for a token first. If still absent, do not run `git push` (it will hang) — commit locally, explain the blocker, and ask the user to connect GitHub with write access (Replit GitHub integration or a PAT secret).

**Divergent-history merge conflicts (e.g. a co-developer/IDE agent pushed their own commits to the same remote while this workspace worked locally):** the sandbox git CLI here cannot resolve this itself — `git merge` with real conflicts needs a `git commit` to finalize, and `git commit`/`git push` are off-limits or non-functional in this environment. Resolve at the *content* level instead: diff `origin/<branch>` against the merge-base and against local HEAD per file, manually combine the best of both into the working tree (plain file edits, not git commands), verify (e.g. compile), and tell the user the local/remote histories are still diverged — they must use Replit's own Git panel (which has separate, working push credentials distinct from the sandbox `origin` remote) to pull and finalize, keeping "this workspace's version" for the files already merged.
