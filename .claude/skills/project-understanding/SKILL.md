---
name: project-understanding
description: Use at the start of any session or task to restore full context on the Amex Campus Challenge R1 — what we're solving, the constraints, and current state. Invoke before acting when unsure of scope.
---

# Project Understanding

## Purpose
Rebuild accurate context fast so no session re-derives known facts or violates a constraint.

## Inputs
`CLAUDE.md`; `.claude/memory/` (project-context, business-context, decision-log, experiment-history, roadmap, assumptions).

## Outputs
A correct mental model: the objective, the §16 constraints, the current stage, and the next action.

## Invocation Conditions
- Start of a session or a new task.
- Whenever you're about to make a decision and aren't certain it aligns with prior ones.

## Workflow
1. Read `CLAUDE.md` (esp. §16 constraints, §17 pitfalls).
2. Read `memory/project-context.md` → where are we in the roadmap.
3. Skim `decision-log.md` + `experiment-history.md` → what's decided / tried.
4. Confirm the immediate task fits the roadmap; if it conflicts, surface that before proceeding.

## Best Practices
- Trust memory over assumption, but verify a memory claim if it names a file/number before relying on it.
- If something learned is durable, write it back to the right memory file.

## Common Mistakes
- Diving into code without restoring constraints (re-introduces `id` leakage / overfit).
- Treating the problem as supervised ML (it isn't — see decision-log 2026-06-26).

## Example Usage
"Restore context, then tell me the next roadmap step." → read memory → "Stage 2 (env setup) is next; pandas is broken, use the stdlib reader."
