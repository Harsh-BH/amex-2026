---
description: Systematically debug an unexpected scoring result, crash, or leaderboard surprise.
argument-hint: [the symptom]
---
Invoke the project **debugging** skill (applies `superpowers:systematic-debugging` to this project's usual suspects).

Symptom: $ARGUMENTS

**Expected output:** reproduced minimal case → root cause → minimal fix → a runnable regression check. Fix the cause, not the symptom.

**Internal workflow:** reproduce → isolate → check usual suspects (broken pandas stub, NaN propagation, scale dominance, non-determinism, submission-format reject) → verify → fix + check.
