---
name: refactoring
description: Use when scoring/pipeline code has grown messy or duplicated — consolidate without changing the score. Project-scoped; delegates simplification depth to the global /simplify skill. Behavior-preserving only.
---

# Refactoring (project-scoped)

## Purpose
Improve structure/readability of the scoring pipeline **without changing the output** — and resist adding speculative structure.

## Inputs
The code to refactor; existing runnable checks.

## Outputs
Cleaner code; identical `Prediction` output (verified).

## Invocation Conditions
- Code smells (duplication, scattered weights/constants, notebook logic that should be in `src/`).

## Workflow
1. Ensure a check exists that pins current behavior (golden score on a sample, or full-file hash).
2. Run **/simplify** for the cleanup pass.
3. Consolidate weights/config into `config.py` (`standards/configuration.md`); move reused logic into `src/`.
4. **Verify the score is byte-identical** before/after (deterministic).
5. Don't add abstraction for a single use (Ponytail).

## Best Practices
- Behavior-preserving; one refactor at a time; re-run the pin.

## Common Mistakes
- "Refactoring" that silently changes the score (no pin to catch it).
- Adding factories/configs/interfaces the competition will never need.

## Example Usage
"Clean up scoring.py." → pin golden scores → /simplify → centralize weights → confirm identical output.
