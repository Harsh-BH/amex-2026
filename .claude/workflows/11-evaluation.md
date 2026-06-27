# Workflow 11 — Evaluation

**Objective:** Estimate top-20% overlap quality internally and gate submissions.
**Prerequisites:** Workflows 09–10.

## Steps
1. Invoke **evaluation** (`/evaluate`).
2. Compute top-20% cutoff; run repeated 70/30 resamples; measure top-quintile membership stability.
3. Weight/transform sensitivity; score-distribution sanity (no degenerate ties).
4. Plausibility spot-check of top members (**business-analysis**).
5. Decide keep/kill; record.

## Validation
- Stable top-20% across resamples; clean distribution; plausible top members.

## Deliverables
- Validation metrics in the experiment record.

## Exit criteria
- Confidence the score generalizes → proceed to submission or iterate.
