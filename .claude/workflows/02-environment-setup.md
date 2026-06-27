# Workflow 02 — Environment Setup & Dataset Validation

**Objective:** A working, reproducible env that can read the dataset, and a validated dataset.
**Prerequisites:** Workflow 01 done.

## Steps
1. Verify `pandas`/`openpyxl` actually work (`pd.__version__`). The sandbox ships broken stubs — if so, fix the env or commit to the stdlib `zipfile`+`xml` reader.
2. Pin the env → `requirements.txt`.
3. Load the dataset; **assert** shape (500,000 × 24) and columns (`id`,`f1`–`f23`), numeric dtypes.
4. Re-confirm structural facts vs `memory`: missingness clusters (A2–A4), `f7` negatives (A6), `f5` scale (A1).

## Validation
- Data loads deterministically by column name; asserts pass; ranges match `feature-notes.md`.

## Deliverables
- `requirements.txt`; a reusable `src/io.py` loader with the fallback reader.

## Exit criteria
- One command loads & validates the data; env reproducible.
