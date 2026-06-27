---
description: Build/calibrate the profitability scoring framework (this problem has no model to "train" — it fits an interpretable equation).
argument-hint: [framework change or "draft v1"]
---
Invoke **profitability-framework-design**, then **weight-calibration**. This is framework design, NOT supervised training (no label exists).

Request: $ARGUMENTS

**Expected output:** updated `src/scoring.py` (revenue−cost equation) + weight table + `templates/framework-doc.md`, with every term justified.

**Internal workflow:** structure P&L → map features → normalize → weight (business prior) → combine sign-correct → hand-built ranking check → document. Then run `/evaluate` before any submission.
