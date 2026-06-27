---
name: weight-calibration
description: Use to set and tune the weights/coefficients of the profitability equation — by business reasoning first, then careful leaderboard-informed calibration. Replaces generic hyperparameter tuning; guard against overfitting the public 70%.
---

# Weight Calibration

## Purpose
Choose the weights that combine the revenue/cost terms, balancing business priors with limited leaderboard feedback, without overfitting.

## Inputs
The framework equation; business priors on relative magnitudes; public-LB results in `experiment-history.md`.

## Outputs
A weight table (`templates/model-doc.md`) with rationale + sensitivity analysis.

## Invocation Conditions
- After a framework structure exists; whenever adjusting term importance.

## Workflow
1. **Prior:** set weights from business magnitude (interchange revenue typically dominates; risk discounts revenue, not adds noise).
2. **Normalize** terms first so weights mean what they say.
3. **Sensitivity:** perturb each weight ±X%; see how much the **top-20% membership** moves. Robust weights > knife-edge.
4. **Calibrate sparingly** against the public LB — only changes that are *also* business-justified. Log each as an experiment.
5. **Overfit guard:** prefer simpler weighting that generalizes; treat a public-LB gain with no business story as a red flag for the private 30%.

## Best Practices
- Spend internal-validation effort before spending a submission.
- Track which members enter/leave the top 20% per weight change, not just the score.

## Common Mistakes
- Grid-searching weights purely to climb the public LB (overfit → private-LB drop).
- Tuning before normalizing (weights become uninterpretable).
- Burning submissions to test what an internal resample could answer.

## Example Usage
"Tune the risk weight." → raise risk discount, check top-20% churn + sensitivity; if stable and business-sound, log exp and consider a submission.
