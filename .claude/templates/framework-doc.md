# Profitability Framework — Submission Writeup
<!-- Mirrors the `Profitability Framework` sheet in the submission template.
     Keep this current as the equation evolves; the sheet is a graded deliverable. -->

## Variables Used
<!-- List the f-codes used + decoded name + role (revenue/cost). Justify exclusions of the rest. -->

## Profitability Equation
<!-- The explicit equation. profit_score = Σ (weight × transformed feature). Show it plainly. -->

## Prediction Logic
<!-- How the equation becomes the `Prediction` score and how it rank-orders members to a top-20% cut. -->

## Variable Selection Logic
<!-- Why each feature is in/out, tied to the P&L (business-context.md). Why id and constant-fee are excluded. -->

## Coefficient / Weight Derivation
<!-- How weights were set: business reasoning, normalization, any leaderboard calibration. Reproducible. -->

## Feature Transformations
<!-- Scaling/normalization, missing-value rule per cluster (A2–A4), f7 negatives (A6), f5 handling (A1). -->

## Business Logic
<!-- The economic story: revenue terms, cost terms, risk adjustment. Why a high score = a profitable CM. -->

## Assumptions
<!-- Pull the relevant rows from memory/assumptions.md; state which are verified vs assumed. -->

## Validation Approach
<!-- Top-20% stability across resamples; sensitivity to weights; guard against public-LB overfit. -->

## Additional Notes (Optional)
<!-- Limitations, real-world scalability, ideas not yet tried. -->
