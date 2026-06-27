# Standard — Logging

- Use the stdlib `logging` module, not `print`, in `src/` and `score.py`. `print` is fine in notebooks.
- **Log the things that make a run auditable:** rows loaded, missing counts per feature cluster, weights/config used, score distribution summary, top-20% cutoff value, rows written.
- One INFO line per pipeline stage (load → clean → score → validate → write). DEBUG for per-feature detail.
- Always log the **submission filename + seed + experiment #** at the end of a scoring run so the log ties to `experiment-history.md`.
- Never log PII (there is none here) or full data dumps. Log summaries, not 500K rows.
- Keep logs deterministic-friendly: no timestamps inside anything that gets diffed for reproducibility.
