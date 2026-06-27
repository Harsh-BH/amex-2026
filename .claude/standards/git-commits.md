# Standard — Git Commits & Workflow

- Trunk = `main`. Work on `<stage>/<slug>` branches (`eda/missingness`, `framework/revenue-cost-v1`).
- **Commit/push only when the user asks.** If on `main`, branch first.
- Message: imperative subject ≤72 chars; body explains **why**, links the experiment/decision.
  - e.g. `framework: add risk-adjusted interest term` / body: "f17×(1−f11) margin proxy; exp-004; +1.8 public LB".
- **Never commit:** the dataset or any `docs/` file, generated submissions, `data/`, large binaries, secrets. Keep `.gitignore` covering `data/`, `submissions/`, `*.xlsx` outputs, `__pycache__`.
- One logical change per commit. Don't mix EDA notebook noise with scoring logic.
- Co-author trailer on commits as configured; PR bodies summarize the change + its LB effect.
- Tag the commit behind each submission (`submit-vN`) so the exact scoring code is recoverable.
