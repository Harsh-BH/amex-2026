---
name: documentation
description: Use when writing or updating any project documentation — especially the graded Profitability Framework writeup, and keeping memory/ current. Invoke via /document.
---

# Documentation

## Purpose
Keep the project explainable: the Framework writeup (graded), memory state (continuity), and reports (for R2/R3).

## Inputs
The thing to document; relevant templates and memory.

## Outputs
Updated `templates/framework-doc.md`, `memory/` files, or a `report.md` — accurate and current.

## Invocation Conditions
- After any decision, experiment, or scoring change; before submission/delivery.

## Workflow
1. Pick the right home: framework → `framework-doc.md`; decision → `decision-log.md`; fact/assumption → `assumptions.md`/`feature-notes.md`; experiment → `experiment-history.md`; narrative → `report.md`.
2. Write *why*, not just *what*; tie numbers to business rationale.
3. Ensure the writeup **matches the actual scoring code** — no drift.
4. Keep `CLAUDE.md`/memory truthful; delete stale claims.

## Best Practices
- Maintain the Framework writeup continuously — submission should be copy-paste.
- Durable knowledge goes in memory, not buried in code comments.

## Common Mistakes
- Framework sheet describing a different equation than the code (auto-fail risk).
- Letting memory go stale (worse than no memory).

## Example Usage
"/document the v3 framework." → update each framework-doc section to match `scoring.py`, refresh assumptions, note validation result.
