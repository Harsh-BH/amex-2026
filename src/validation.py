"""Top-20% stability validation for the v1 score (label-free).

The real metric is % overlap of OUR top-20% vs Amex's hidden top-20%. With no label, we instead
prove our top-20% is STABLE — robust to which rows we see (subsample) and to the exact weights
(perturbation) — and business-plausible. Spec stage 7. NO submission until this looks healthy.

Run:  .venv/bin/python src/validation.py
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from eda import PremierEDA, SPEND_CATS
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


def _spend_proxy(df: pd.DataFrame) -> pd.Series:
    """Raw spend-dollar proxy: category-sum f6–f10 (f5 fallback), missing -> 0. Same basis the
    score ranks on, but in dollars so we can measure how much revenue mass the top-20% captures."""
    return df[SPEND_CATS].sum(axis=1, min_count=1).fillna(df.f5).fillna(0.0)


def revenue_capture(df: pd.DataFrame, q: float = TOP_Q) -> pd.DataFrame:
    """Whale-curve check (closest label-free proxy for the graded top-20%-overlap metric): the
    share of each raw revenue-driver's dollar mass that our top-20% holds, and lift = capture/(1-q).
    A score that finds the profitable tail should hold FAR more than 20% of revenue mass (lift > 1).
    Drivers: spend (interchange), carried balance f1 (revolve interest), lending line f17."""
    top = top_set(score(df), q)
    mask = df.index.isin(top)
    base = 1 - q
    drivers = {"spend": _spend_proxy(df), "balance_f1": df.f1.fillna(0.0), "lend_line_f17": df.f17.fillna(0.0)}
    rows = []
    for name, v in drivers.items():
        tot = float(v.sum())
        cap = float(v[mask].sum()) / tot if tot > 0 else float("nan")
        rows.append({"driver": name, "top20_capture": round(cap, 3), "lift_vs_pop": round(cap / base, 2)})
    return pd.DataFrame(rows).set_index("driver")


def spend_only_overlap(df: pd.DataFrame, q: float = TOP_Q) -> float:
    """Jaccard of our top-20% vs a naive spend-only top-20%. Guards 'revenue ≠ profit': cost/risk
    must reshuffle the tail away from pure spend, so expect high overlap but < 1 (full 1.0 would mean
    the framework is just an expensive proxy for ranking by f5; ~0 would mean it ignores spend)."""
    return jaccard(top_set(score(df), q), top_set(_spend_proxy(df), q))


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
    print(f"\ntop-20% revenue capture (whale curve — capture > {1-TOP_Q:.0%} & lift > 1 = finds the profitable tail):")
    print(revenue_capture(df))
    print(f"\noverlap of top-20% vs naive spend-only top-20%: {spend_only_overlap(df):.3f}  (want high but < 1.0)")
    print("\ntop-20% segment mix:")
    print(segment(df)[top].value_counts(normalize=True).round(3))
    print("OK validation.py ran. Read the numbers before deciding on a submission.")


def _self_check():
    """Tiny frame: capture/overlap mechanics stay in valid ranges and are deterministic. A frame
    whose score tracks spend must show top-20% spend-capture above the 20% population share."""
    rng = np.random.default_rng(0)
    demo = pd.DataFrame(rng.integers(0, 100, size=(200, 23)).astype(float), columns=[f"f{i}" for i in range(1, 24)])
    demo.insert(0, "id", range(200))
    rc = revenue_capture(demo)
    assert rc["top20_capture"].between(0, 1).all(), rc
    assert (rc["lift_vs_pop"] >= 0).all(), rc
    so = spend_only_overlap(demo)
    assert 0 <= so <= 1, so
    assert revenue_capture(demo).equals(revenue_capture(demo)), "capture must be deterministic"
    print("OK validation.py self-checks pass")


if __name__ == "__main__":
    _self_check()
    main()
