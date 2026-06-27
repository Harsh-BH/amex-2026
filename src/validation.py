"""Top-20% stability validation for the v1 score (label-free).

The real metric is % overlap of OUR top-20% vs Amex's hidden top-20%. With no label, we instead
prove our top-20% is STABLE — robust to which rows we see (subsample) and to the exact weights
(perturbation) — and business-plausible. Spec stage 7. NO submission until this looks healthy.

Run:  .venv/bin/python src/validation.py
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from eda import PremierEDA
from score import score, segment, WEIGHTS, SEED

TOP_Q = 0.8


def top_set(s: pd.Series, q: float = TOP_Q) -> set:
    return set(s.index[s >= s.quantile(q)])


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a | b) else 1.0


def subsample_stability(df: pd.DataFrame, n: int = 20, frac: float = 0.7, seed: int = SEED) -> float:
    """Mean Jaccard of (top-20% ranked within a frac-subsample) vs (full-data top-20% ∩ that subsample).
    High => the top tail isn't an artifact of which rows happened to be scored."""
    rng = np.random.default_rng(seed)
    base_top = top_set(score(df))
    ov = []
    for _ in range(n):
        idx = rng.choice(df.index.to_numpy(), size=int(len(df) * frac), replace=False)
        sub_top = top_set(score(df.loc[idx]))
        base_top_in_sub = base_top & set(idx)
        ov.append(jaccard(sub_top, base_top_in_sub))
    return float(np.mean(ov))


def weight_perturbation_stability(df: pd.DataFrame, n: int = 15, pct: float = 0.15, seed: int = SEED) -> float:
    """Mean Jaccard of baseline top-20% vs top-20% after jittering every weight by ±pct.
    High => the ranking doesn't hinge on the exact (un-calibrated) weight values."""
    rng = np.random.default_rng(seed + 1)
    base_top = top_set(score(df))
    ov = []
    for _ in range(n):
        w = {k: tuple(max(0.0, x * (1 + rng.uniform(-pct, pct))) for x in v) for k, v in WEIGHTS.items()}
        ov.append(jaccard(base_top, top_set(score(df, w))))
    return float(np.mean(ov))


def main():
    df = PremierEDA().df
    base = score(df)
    assert base.notna().all(), "base score has NaNs"
    sub = subsample_stability(df)
    wpt = weight_perturbation_stability(df)
    assert 0 <= sub <= 1 and 0 <= wpt <= 1
    top = base >= base.quantile(TOP_Q)
    print(f"subsample top-20% stability (Jaccard, mean): {sub:.3f}")
    print(f"weight-perturbation top-20% stability:       {wpt:.3f}")
    print(f"score concentration (Gini):                  {PremierEDA._gini(base):.3f}")
    print("top-20% segment mix:")
    print(segment(df)[top].value_counts(normalize=True).round(3))
    print("OK validation.py ran. Read the numbers before deciding on a submission.")


if __name__ == "__main__":
    main()
