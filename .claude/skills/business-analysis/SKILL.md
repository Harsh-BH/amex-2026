---
name: business-analysis
description: Use when reasoning about issuer profitability economics — which features are revenue vs cost, what makes a Premier cardmember profitable, and how to justify a scoring term in business language. Invoke during framework design and the Framework writeup.
---

# Business Analysis

## Purpose
Translate card-economics into the revenue/cost logic the profitability framework must encode, and produce defensible business justifications (the graded Framework sheet).

## Inputs
`.claude/memory/business-context.md`, `feature-notes.md`, the Premier Card product overview (problem PDF).

## Outputs
A revenue/cost mapping per feature; a plain-language rationale for each scoring term.

## Invocation Conditions
- Deciding whether/how a feature enters the score.
- Writing or reviewing the `Profitability Framework` sheet.
- Sanity-checking whether a top-20% member "makes business sense".

## Workflow
1. For the feature/term, classify: revenue, cost, or risk-adjustment — cite the mechanism (interchange, interest, rewards, benefit credit, loss, servicing).
2. State expected direction on profit and magnitude intuition.
3. Note interactions (e.g. spend drives both interchange revenue and rewards cost).
4. Write the one-paragraph justification for the writeup.

## Best Practices
- Anchor to a real P&L line, not a vibe. Annual fee is constant → never a ranking term.
- Prefer ratios that capture margin (e.g. benefit cost *relative to* spend) over raw magnitudes when arguing profitability.

## Common Mistakes
- Counting spend as pure profit (ignores rewards/benefit cost it generates).
- Treating revolve/lend as pure revenue (ignores credit risk `f11`/`f3`).

## Example Usage
"Justify including f13 (lounge)." → "Lounge visits are an issuer-paid benefit cost; high usage without offsetting spend erodes margin → enters the score as a cost term, ideally normalized by spend."
