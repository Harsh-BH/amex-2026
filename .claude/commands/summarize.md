---
description: Produce a concise status summary of the project for a human or for session handoff.
argument-hint: [optional audience, e.g. "teammate" or "for R2 handoff"]
---
Invoke **project-understanding**, then summarize.

Audience: $ARGUMENTS (default: self/handoff)

**Expected output:** a tight status: roadmap stage, best submission + score, key decisions, open assumptions, submission budget used, and the next action. Pull from `memory/`.

**Internal workflow:** read memory (project-context, roadmap, experiment-history, decision-log, assumptions) → 5–8 bullet summary → next step.
