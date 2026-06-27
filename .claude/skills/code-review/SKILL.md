---
name: code-review
description: Use before merging scoring/pipeline code. Project-scoped review for the two failure modes that matter here — leakage/correctness bugs and over-engineering. Delegates depth to the global /code-review and /simplify skills.
---

# Code Review (project-scoped)

## Purpose
Catch the project's specific correctness traps and unnecessary complexity before merge.

## Inputs
The diff/branch; `templates/code-review.md`; `standards/`.

## Outputs
Findings (file:line, issue, fix) + verdict.

## Invocation Conditions
- Before merging any code touching scoring, IO, or the submission builder.

## Workflow
1. Run the global **/code-review** for general correctness, and **/simplify** for over-engineering — they do the heavy lifting.
2. Add the **project must-checks** (these are non-negotiable here):
   - `id` never used as a feature; no split leakage.
   - Missing-value rule applied; no stray NaN/blind `fillna(0)`.
   - Scales normalized before weighting; `f5`/`f7` traps avoided (A1, A6).
   - Deterministic; output exactly 500K valid rows; submission builder guards format.
3. Fill `templates/code-review.md`; give a verdict.

## Best Practices
- Correctness first, then complexity. One clear fix per finding.

## Common Mistakes
- Approving code that silently re-introduces `id` or alters row count.

## Example Usage
"Review the scoring branch." → /code-review + /simplify, then verify no `id` leakage and 500K-row guard present.
