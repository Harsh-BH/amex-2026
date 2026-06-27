# Standard — Naming Conventions

## Code
- `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE` for constants.
- Scoring weights: `W_<COMPONENT>` (e.g. `W_SPEND`, `W_RISK`) — name reveals the P&L role.
- Feature references keep the masked code AND a comment: `df["f7"]  # Other Spend (has refunds)`.

## Files & artifacts
- Scripts: verb-first, `score.py`, `build_eda.py`, `make_submission.py`.
- Submissions: `submission_v<N>_<short-desc>.xlsx` (e.g. `submission_v3_riskadj.xlsx`). `<N>` matches experiment-history index.
- Experiment records: `exp-<NNN>-<slug>.md`.
- Plots: `eda_<feature-or-topic>.png`.
- Branches: `<stage>/<slug>` (e.g. `framework/revenue-cost-v1`, `eda/missingness`).

## Memory & docs
- Memory files stay as named in `.claude/memory/` — don't rename (CLAUDE.md points to them).
- Never invent new names for the official feature codes; always `f1`–`f23` + decoded name from `terminology.md`.
