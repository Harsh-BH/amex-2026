# CLAUDE.md — Master Operating Manual

> Auto-loaded every session. Keep it lean: the *rules and pointers* live here;
> the *detail* lives in `.claude/` and is loaded on demand. Read `.claude/README.md`
> for the map of this operating system.

---

## 1. Project Overview

**American Express Campus Challenge 2026 — Round 1: "Measuring Customer Profitability for the Premier Card."**

We must **rank-order 500,000 Premier cardmembers by their profitability to the issuer** and
submit (a) a profitability **score per `id`** for every row, and (b) a written
**Profitability Framework** explaining the equation and its business logic.

This is a **3-round competition**: R1 = data/analytical (this repo's focus), R2 = case study,
R3 = deck presentation. Top performers earn PPIs and prizes.

## 2. Business Context

The Premier Card is an ultra-premium charge card (annual fee $500–750; target: high-income
frequent travelers). The issuer earns from **spend (interchange), interest/lending, and fees**,
and pays out **rewards, lifestyle/travel credits, lounge access, insurance, and credit losses**.
We are estimating **profit to the issuer ≈ revenue − cost** per cardmember.

- Revenue levers: spend (`f5`–`f10`), revolve/lend interest (`f1`,`f17`,`f18`), supp & cards (`f19`,`f20`).
- Cost levers: rewards (`f4`,`f21`), benefit credits (`f13`–`f16`), credit risk (`f11`,`f3`), servicing/attrition (`f2`).
- Annual fee is **constant within the product** → it does **not** differentiate members.

Full business reasoning: `.claude/memory/business-context.md`. Per-feature P&L direction: `.claude/memory/feature-notes.md`.

## 3. Technical Context

- **Data:** one sheet, `docs/6a3cb6104933b_campus_challenge_r1_data.xlsx`, **500,000 rows × 24 cols** (`id`, `f1`–`f23`), all numeric. **No target/label column exists.**
- **This is NOT supervised learning.** There is no profitability label to train on. We **design an interpretable revenue−cost framework** whose ranking matches Amex's hidden ground truth. Black-box ML that can't be explained in the Framework sheet is the wrong tool here.
- **Dictionary:** `docs/6a3cb624df197_feature_description.xlsx` (decoded in `.claude/memory/terminology.md`).
- **Submission:** `docs/6a3cb64c7cae4_campus_challenge_r1_submission_template.xlsx` — two sheets: `Predictions` (`ID, Prediction` for all 500K) and `Profitability Framework` (qualitative writeup).
- **Stack:** Python 3.11+, pandas/numpy (polars optional), matplotlib. Heavy ML frameworks are usually unnecessary. ⚠ The sandbox's `pandas`/`openpyxl` are broken stubs — verify the env (`.claude/standards/reproducibility.md`) before trusting them; stdlib `zipfile`+`xml` reads the xlsx if needed.

## 4. Architecture Principles

1. **Interpretability over accuracy-at-any-cost.** Every term in the score must map to a revenue or cost the issuer actually books. The Framework writeup is graded.
2. **Rank, don't label.** Only the relative ordering at the **top 20%** matters.
3. **Reproducible by default.** Fixed seeds, pinned deps, deterministic scoring. Anyone can re-run and get the same file.
4. **Missingness is a signal, not noise** — treat it deliberately (`.claude/skills/missing-value-analysis`).
5. **No leakage, no gaming.** Never use `id`. Never overfit the public 70%.

## 5. Development Philosophy

Lazy-but-correct (see global Ponytail). Smallest thing that works, stdlib before deps,
one interpretable equation before a model zoo. Build the score, validate the top-20%
separation, write down *why*. Don't add structure the competition doesn't need.

## 6–10. Standards (pointers)

- **Coding / Python:** `.claude/standards/python.md`
- **Naming conventions:** `.claude/standards/naming-conventions.md`
- **Documentation:** `.claude/standards/documentation.md`
- **Testing philosophy:** `.claude/standards/testing.md` — every non-trivial transform leaves one runnable check.
- **Error handling:** `.claude/standards/error-handling.md`
- **Logging:** `.claude/standards/logging.md`
- **Config:** `.claude/standards/configuration.md`
- **Reproducibility:** `.claude/standards/reproducibility.md`
- **Folder structure:** `.claude/standards/folder-structure.md`

## 11. Experiment Guidelines

Every scoring attempt is an **experiment** with a hypothesis, a recorded config, a
public-LB result, and a keep/kill decision. Use `.claude/templates/experiment.md`,
log to `.claude/memory/experiment-history.md`. **Submissions are capped at 10** — never
burn one without a hypothesis. See `.claude/skills/experiment-tracking`.

## 12. Prompting Standards

When delegating to subagents (`.claude/agents/`), give them the constraint set from §16,
the data dictionary, and a structured-output contract. Reusable analytical prompts are
codified as **skills** (`.claude/skills/`), not pasted ad hoc.

## 13. Git Workflow

Trunk = `main`. Branch per stage (`eda/…`, `framework/…`, `submit/…`). Commit messages:
imperative subject, body explains *why*. Never commit data files, secrets, or generated
submissions. See `.claude/standards/git-commits.md`. Commit/push only when asked.

## 14. Repository Rules

- `docs/` = the official challenge files (read-only; never edit).
- Generated submissions go to `submissions/` (git-ignored), named `submission_v<N>_<desc>.xlsx`.
- Never alter, add rows to, or reorder the shared dataset.
- The solution must score **all** `unique_identifiers`.

## 15. Project Roadmap

Living plan in `.claude/memory/roadmap.md`. High level: Understand → EDA → Missing-value
strategy → Framework design → Calibrate weights → Score 500K → Validate top-20% → Submit →
Iterate (≤10) → Document. Then R2/R3.

## 16. Important Constraints (NON-NEGOTIABLE)

1. **Never use `id`** (or any identifier) as a predictor — instant gaming/leakage.
2. **Use only existing variables** `f1`–`f23`. No external data.
3. **Do not add rows or alter the shared data.**
4. **Score every one of the 500K rows.** No nulls in the `Prediction` column.
5. **≤10 submissions.** Best score counts. Don't overfit the public 70% — a hidden 30% decides placement.
6. **Metric = % overlap of our Top-20% vs Actual Top-20%.** Optimize top-tier separation, not global rank.
7. **Follow the exact Unstop submission template.** Both sheets.
8. Solution must be **scalable & explainable** (Amex audits for integrity/gaming; plagiarism = DQ).

## 17. Common Pitfalls

- Treating it as labeled ML and inventing a target to "train" on.
- Assuming `f5` (Total Spend, max ≈13.6K) = sum of `f6`–`f10` (it is **not** — scale/definition differs; see `.claude/memory/assumptions.md`).
- Filling missing with 0 blindly (missingness is structured: `f6`–`f10` co-miss; `f4`/`f21` co-miss; `f17`/`f18` ≈60% missing = charge-only members).
- Forgetting `f7` has **negative** values (refunds).
- Mixing wildly different scales (`f11`≈0.03 vs `f4`≈126K) in a weighted sum without normalization.
- Overfitting the public leaderboard across the 10 submissions.
- Producing a high score with no defensible business logic for the Framework sheet.

## 18. Claude Operating Instructions

- **Start of session:** skim this file + `.claude/memory/` (project-context, decision-log, experiment-history, roadmap) to restore state.
- **Pick the right entry point:** slash commands in `.claude/commands/` for routine tasks; skills in `.claude/skills/` for how-to depth; workflows in `.claude/workflows/` for end-to-end stages.
- **Before claiming done:** run the relevant checklist in `.claude/checklists/`.
- **Persist what you learn:** update the right `.claude/memory/` file (decisions → decision-log, experiments → experiment-history, new facts/assumptions → assumptions). Memory is the project's long-term brain.
- **Respect §16 always.** When unsure, re-read the constraints before acting.
