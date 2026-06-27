---
name: debugging
description: Use when scoring output, the pipeline, or a leaderboard result is unexpected. Project-scoped entry point that applies systematic debugging to this project's likely failure points. Delegates method to superpowers:systematic-debugging.
---

# Debugging (project-scoped)

## Purpose
Find root causes of wrong scores / broken runs / surprising LB results without guess-and-check.

## Inputs
The symptom; logs; the scoring code + config.

## Outputs
Root cause + minimal fix + a regression check.

## Invocation Conditions
- Any bug, crash, or unexpected scoring/LB behavior.

## Workflow
1. Invoke **superpowers:systematic-debugging** for the method (reproduce → isolate → hypothesize → verify).
2. Check this project's usual suspects first:
   - Broken `pandas`/`openpyxl` stub (use stdlib reader).
   - `fillna`/NaN propagation distorting scores.
   - Scale mismatch letting one term dominate.
   - Non-determinism (unset seed, row-order dependence).
   - Submission builder rejecting the file (row count / nulls / template).
3. Reproduce minimally; fix the cause, not the symptom; leave a runnable check.

## Best Practices
- One hypothesis at a time; confirm before fixing.

## Common Mistakes
- Patching the symptom (e.g. `fillna(0)` to silence a NaN) and masking the real cause.

## Example Usage
"Scores are all NaN for some rows." → systematic-debug → trace to un-handled `f6`–`f10` co-missing cluster → apply documented rule + assert no NaN.
