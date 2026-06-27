# Workflow 10 — Weight Calibration

**Objective:** Weights that balance business priors with limited LB feedback, robust to the hidden 30%.
**Prerequisites:** Workflow 09.

## Steps
1. Invoke **weight-calibration**.
2. Set priors from business magnitude (revenue dominates; risk discounts).
3. Sensitivity-test each weight; measure top-20% membership drift.
4. Calibrate against public LB only with business-justified changes; log each as an experiment.
5. Centralize weights in `config.py` (`standards/configuration.md`).

## Validation
- Weights are interpretable, robust to ±perturbation, and not knife-edge.

## Deliverables
- Weight table (`model-doc.md`) + sensitivity notes.

## Exit criteria
- Stable, defensible weights; ready for full evaluation.
