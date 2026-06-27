# `.claude/` — Project Operating System

This directory is the **internal operating system** for the Amex Campus Challenge 2026 (R1)
project. It lets Claude restore context, follow engineering standards, run repeatable
workflows, and retain decisions across sessions.

**Start here, then read `../CLAUDE.md` (auto-loaded master manual).**

---

## How the pieces fit together

```
../CLAUDE.md          ← master manual (auto-loaded). Rules + pointers.
.claude/
├── README.md         ← this map
├── settings.json     ← permissions / env (fewer prompts on safe read commands)
├── commands/         ← slash-command entry points (thin; invoke skills/workflows)
├── skills/           ← reusable HOW-TO expertise (the deep knowledge)
├── workflows/        ← ordered, end-to-end lifecycle processes (sequence skills)
├── agents/           ← subagent role definitions for delegated/parallel work
├── standards/        ← engineering guardrails (Python, repro, git, …)
├── checklists/       ← gates to run before code / experiments / submission / merge
├── templates/        ← fill-in forms (experiment, framework doc, PR, report, …)
└── memory/           ← persistent project state (the long-term brain)
```

**Mental model of the layers:**

- **Knowledge** lives in `skills/` (how to do a thing well) and `standards/` (the rules).
- **Process** lives in `workflows/` (multi-step stages) and `checklists/` (gates).
- **Entry points** are `commands/` (quick triggers) and `agents/` (delegated roles).
- **Forms** are `templates/`. **State** is `memory/`.

Typical flow: a **command** (`/eda`) triggers a **skill** (`eda`) which follows a
**standard** (`reproducibility.md`), produces output recorded via a **template**
(`research-notes.md`) into **memory** (`feature-notes.md`), gated by a **checklist**
(`before-experiments.md`). **Workflows** chain several of these for a whole stage.

---

## Folder reference

### `commands/` — slash-command entry points
- **Purpose:** one-word triggers for recurring tasks.
- **Why:** lower friction; encode the project's specifics so you don't re-type intent.
- **When:** any routine action (`/eda`, `/features`, `/submit`, `/review`).
- **Contains:** thin `*.md` files that mostly *invoke a skill or workflow* with project paths.
- **Interacts with:** `skills/` and `workflows/` (delegates to them); `memory/` (logs results).

### `skills/` — reusable how-to expertise
- **Purpose:** the deep, reusable knowledge for each analytical activity.
- **Why:** consistency — the *right* way to do EDA / missing-value analysis / framework design, every time.
- **When:** whenever doing that activity, directly or via a command/workflow.
- **Contains:** `<skill-name>/SKILL.md` (frontmatter `name`,`description` + workflow, best practices, pitfalls, example).
- **Interacts with:** invoked by `commands/` & `workflows/`; cites `standards/`; writes to `memory/`.

### `workflows/` — end-to-end lifecycle processes
- **Purpose:** ordered procedures for a whole stage (e.g., "build & submit a scored framework").
- **Why:** repeatability and exit criteria for multi-step work.
- **When:** at the start of a stage, or to resume one.
- **Contains:** `*.md` with Objective / Prerequisites / Steps / Validation / Deliverables / Exit criteria.
- **Interacts with:** sequences `skills/`; ends with a `checklists/` gate; updates `memory/roadmap.md`.

### `agents/` — subagent role definitions
- **Purpose:** specialized personas for delegated or parallel work (explore, critique, validate).
- **Why:** isolate context-heavy or adversarial tasks; run independent work in parallel.
- **When:** large fan-out reads, red-teaming the framework, validating a submission file.
- **Contains:** `*.md` with frontmatter (`name`,`description`,`tools`,`model`) + role brief.
- **Interacts with:** dispatched by the main session; pointed at `skills/` + `memory/` for context.

### `standards/` — engineering guardrails
- **Purpose:** the non-negotiable "how we write/run things."
- **Why:** quality, reproducibility, reviewability.
- **When:** writing any code, configuring runs, committing.
- **Contains:** short focused `*.md` (python, naming, docs, logging, testing, git-commits, configuration, error-handling, reproducibility, folder-structure).
- **Interacts with:** cited by `skills/`, enforced by `checklists/`.

### `checklists/` — gates
- **Purpose:** stop-and-verify before risky/irreversible steps.
- **Why:** prevent the classic failures (id leakage, bad submission format, overfit, dirty merge).
- **When:** before writing code, running experiments, training/scoring, submitting, merging, final delivery.
- **Contains:** `*.md` ticklists with pass/fail criteria.
- **Interacts with:** referenced at the end of `workflows/`; enforce `standards/` & §16 constraints.

### `templates/` — fill-in forms
- **Purpose:** consistent structure for recurring artifacts.
- **Why:** nothing important gets recorded ad hoc or forgotten.
- **When:** logging an experiment, documenting a feature/framework, opening a PR, writing a report.
- **Contains:** `*.md` skeletons (experiment, feature-doc, framework-doc, report, research-notes, pull-request, code-review, meeting-notes).
- **Interacts with:** outputs land in `memory/`; used by `skills/` & `workflows/`.

### `memory/` — persistent project state (the long-term brain)
- **Purpose:** what Claude must remember across sessions.
- **Why:** continuity — decisions, assumptions, experiment results, terminology survive context resets.
- **When:** read at session start; updated whenever something durable is learned/decided.
- **Contains:** project-context, business-context, assumptions, feature-notes, terminology, decision-log, experiment-history, roadmap.
- **Interacts with:** read/updated by everything; the source of truth for project state.

---

## Consolidations (deliberate — see Final Review)

To avoid redundant scaffolding, these requested folders were folded into existing ones:

| Requested | Folded into | Why |
|---|---|---|
| `claude.md` | root **`CLAUDE.md`** | Only root `CLAUDE.md` is auto-loaded by Claude Code (case-sensitive). |
| `context/` | `memory/` | "Context" *is* persistent state. One brain, not two. |
| `prompts/` | `skills/` + `commands/` | Reusable prompts are codified as skills/commands, not loose text. |
| `docs/` | repo `../docs/` + `memory/terminology.md` | Official files already live in `../docs/`; the decoded dictionary lives in memory. |
| `experiments/` | `memory/experiment-history.md` + `templates/experiment.md` | Experiment *records* are memory; experiment *code/outputs* live outside `.claude/`. |
| `examples/` | `templates/` | A filled-in example is just a template with sample content. |
