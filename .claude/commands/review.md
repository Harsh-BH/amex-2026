---
description: Review scoring/pipeline code for correctness + over-engineering before merge.
argument-hint: [branch/diff or file]
---
Invoke the project **code-review** skill (which runs global `/code-review` + `/simplify`, then the project must-checks).

Target: $ARGUMENTS (default: current diff)

**Expected output:** findings (file:line, issue, fix) + verdict, filled into `templates/code-review.md`. Hard-gate on: no `id` leakage, missing-value rule applied, scales normalized, deterministic, 500K-row submission guard.

**Internal workflow:** /code-review → /simplify → project must-checks → verdict.
