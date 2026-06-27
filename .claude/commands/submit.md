---
description: Build and validate the submission file against the exact template (CRITICAL — guards the 10-submission budget).
argument-hint: [version/description, e.g. "v3 riskadj"]
---
Run the **`before-submission` checklist** in full before producing the file.

Version: $ARGUMENTS

**Expected output:** `submissions/submission_v<N>_<desc>.xlsx` with BOTH sheets: `Predictions` (exactly 500K rows, all `id`s once, no null `Prediction`) and `Profitability Framework` (from `templates/framework-doc.md`). Experiment logged, scoring code committed/tagged.

**Internal workflow:** verify scoring is final & deterministic → build both sheets → run every item in `checklists/before-submission.md` → refuse to emit if any guard fails → log experiment + decrement budget.
