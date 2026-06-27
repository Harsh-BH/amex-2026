# Standard — Python

- **Version:** Python 3.11+. **Stack:** pandas, numpy, matplotlib. polars optional for the 500K rows. No heavy ML deps unless a decision-log entry justifies one (this is a framework problem, not a Kaggle GBM race).
- **Sandbox warning:** the env's `pandas`/`openpyxl` are broken stubs. Verify with `import pandas as pd; pd.__version__` before use. Fallback xlsx reader = stdlib `zipfile` + `xml.etree` (already proven to work on this dataset).
- **Style:** PEP 8, type hints on public functions, f-strings, `pathlib` over `os.path`. Format with `black`, lint with `ruff` if available.
- **Functions small & pure** where possible — a scoring function takes a dataframe, returns a Series; no hidden global state.
- **Vectorize** over Python loops on 500K rows. Avoid `.iterrows()`.
- **Determinism:** set seeds (`np.random.seed`), avoid relying on dict/set ordering for anything scored.
- **No magic numbers** in the scoring equation — every weight is a named constant with a comment tying it to a business rationale (`business-context.md`).
- **One entry point** for scoring (`score.py`) that reads data → produces the submission file, runnable end-to-end with one command.
