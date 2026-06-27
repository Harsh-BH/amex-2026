# Standard — Folder Structure

Project layout outside `.claude/` (created as work proceeds; not built yet — no app code per current scope):

```
amex-2026/
├── CLAUDE.md                # master manual (auto-loaded)
├── .claude/                 # operating system (this)
├── docs/                    # OFFICIAL challenge files — read-only, never edit
├── data/                    # any derived/intermediate data (git-ignored)
├── notebooks/               # exploratory analysis (cleaned before commit)
├── src/                     # reusable code: io, features, scoring, validation
│   ├── io.py                #   load data (with the stdlib xlsx fallback)
│   ├── features.py          #   transforms / missing-value handling
│   ├── scoring.py           #   the profitability equation
│   └── validation.py        #   top-20% stability checks
├── score.py                 # single entry point: data -> submission file
├── submissions/             # generated files (git-ignored), versioned by experiment #
├── reports/                 # EDA reports, figures, final writeups
└── requirements.txt         # pinned env
```

Rules:
- `docs/` is sacrosanct (read-only). `data/`, `submissions/` are git-ignored.
- Keep scoring logic in `src/scoring.py`, not scattered across notebooks.
- Notebooks are for exploration; promote anything reused into `src/`.
