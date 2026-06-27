---
description: Engineer/select features for the profitability framework.
argument-hint: [feature idea or "review current feature set"]
---
Invoke **feature-engineering** and **feature-selection** skills. Only `f1`–`f23` (+ flags derived from them); never `id`.

Request: $ARGUMENTS

**Expected output:** derived/transformed features with documented rationale (`templates/feature-doc.md`), in/out decisions, and runnable checks. Interpretable transforms only.

**Internal workflow:** scale → margin ratios → risk adjustment → structural flags → selection by P&L relevance + signal quality → document.
