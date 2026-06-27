---
description: Run exploratory data analysis on the dataset (or a given feature/topic).
argument-hint: [feature(s) or topic, e.g. "spend features" or "f11 risk"]
---
Invoke the **exploratory-data-analysis** skill. Use the stdlib xlsx reader if pandas is broken (`standards/python.md`).

Target: $ARGUMENTS (default: full-dataset overview)

**Expected output:** captioned figures + a short report (`templates/report.md`) with takeaways, plus updates to `memory/feature-notes.md`. Always inspect the top tail (only top-20% is scored).

**Internal workflow:** load → univariate + missingness + relationships + segments → takeaways → persist to memory. Never use `id`.
