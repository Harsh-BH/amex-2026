---
description: Start/log a scoring experiment (protects the ≤10 submission budget).
argument-hint: [one-line hypothesis]
---
Invoke the **experiment-tracking** skill.

Hypothesis: $ARGUMENTS

**Expected output:** a new `exp-NNN` record (`templates/experiment.md`) + a row in `memory/experiment-history.md`; config + seed captured; internal validation run before deciding to submit.

**Internal workflow:** hypothesis first → capture config/seed/commit → `/evaluate` internally → keep/kill/submit decision → record. Check the 10-submission budget.
