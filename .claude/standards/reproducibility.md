# Standard — Reproducibility

The whole submission must be regenerable from raw data with one command, deterministically.

- **Pin the environment:** record exact versions (`requirements.txt` / `pip freeze`). The sandbox `pandas`/`openpyxl` are broken — fix or pin a working set before any real run.
- **Seed everything:** `np.random.seed(SEED)` with `SEED` a named constant; no unseeded randomness in scoring or in the 70/30-style internal resampling used for validation.
- **Deterministic IO:** read by column name not position; sort by `id` before writing; write all 500K rows in stable order.
- **One command rebuilds the file:** `python score.py --in docs/...data.xlsx --out submissions/submission_vN.xlsx`.
- **Record the run:** each submission's experiment entry names the script commit/hash, seed, and config so the exact `Prediction` column can be reproduced.
- **No hidden state:** scoring must not depend on row order, machine, or wall-clock.
- **Validation is reproducible too:** fix the seed for any internal train/holdout resampling used to estimate top-20% stability.
