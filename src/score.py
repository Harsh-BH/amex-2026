"""Premier-card profitability score — framework v1.

score = (Revenue − Cost) × (1 − Risk), all term inputs rank-normalized to [0,1],
one equation for all 500K with weights keyed by segment (transactor/revolver/lender).
Spec: .claude/memory/framework-design.md. Uses only f1–f23 (never id).

Run:  .venv/bin/python src/score.py     # self-checks, then scores 500K -> data/scores_v1.csv
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from eda import PremierEDA, SPEND_CATS

SEED = 42
OUT = Path(__file__).resolve().parent.parent / "data" / "scores_v1.csv"

# --- per-segment weights (v1 business priors; calibration = roadmap stage 6) ---
# value = (transactor, revolver, lender). Tilt to where each segment earns.
WEIGHTS = {
    "spending":       (1.00, 0.70, 0.70),   # interchange ≈ spend volume
    "balance_int":    (0.00, 0.80, 0.40),   # carried-balance interest
    "borrow_int":     (0.00, 0.00, 0.80),   # lending-line interest
    "depth":          (0.20, 0.20, 0.20),   # extra cards / supp fees
    "rewards_cost":   (0.50, 0.40, 0.40),   # redeemed + discounted liability
    "perks_cost":     (0.30, 0.30, 0.30),   # lounge/airline/cab/ent credits
    "servicing_cost": (0.15, 0.15, 0.15),   # cancel calls
}
SEGMENTS = ("transactor", "revolver", "lender")
REV_TERMS = ("spending", "balance_int", "borrow_int", "depth")
COST_TERMS = ("rewards_cost", "perks_cost", "servicing_cost")
RISK_A, RISK_B, RISK_CAP = 0.8, 0.2, 0.9   # risk = clamp(a*rank(f11) + b*f3, 0, cap)
REWARDS_LAMBDA = 0.5                        # weight of f4 contingent-liability vs realized f21


def segment(df: pd.DataFrame) -> pd.Series:
    """transactor (charge-only, no balance) / revolver (balance, no lend line) / lender (has lend line)."""
    seg = pd.Series("transactor", index=df.index)
    seg[(df.f1 > 0) & df.f17.isna()] = "revolver"
    seg[df.f17.notna()] = "lender"           # lender rule wins
    return seg


def _rank(s: pd.Series) -> pd.Series:
    return s.rank(pct=True)                    # percentile in [0,1]; NaNs stay NaN


def spend_volume_rank(df: pd.DataFrame) -> pd.Series:
    """Cohort-rank spend onto one [0,1] axis: rank category-sum within the breakdown group,
    rank f5 within the no-breakdown group. Never raw f5 as primary volume (it's saturated)."""
    cats = df[SPEND_CATS].sum(axis=1, min_count=1)     # NaN if all categories missing
    has = cats.notna()
    out = pd.Series(np.nan, index=df.index)
    out[has] = cats[has].rank(pct=True)
    out[~has] = df.loc[~has, "f5"].rank(pct=True)      # fallback; NaN only if f5 also missing
    return out


def revenue_terms(df: pd.DataFrame) -> pd.DataFrame:
    """Each term a [0,1] rank; missing -> 0 (that revenue doesn't exist for the member)."""
    t = pd.DataFrame(index=df.index)
    t["spending"]    = spend_volume_rank(df)
    t["balance_int"] = _rank(df.f1)
    t["borrow_int"]  = df.f17.notna().astype(int) * _rank(df.f17)   # 0 for non-lenders
    t["depth"]       = _rank(df.f19.fillna(0) + df.f20.fillna(0))
    return t.fillna(0.0)


def cost_terms(df: pd.DataFrame) -> pd.DataFrame:
    """Each term a [0,1] rank; missing -> 0 (that cost doesn't exist for the member)."""
    redemption_intensity = df.f21 / (df.f4 + df.f21)               # [0,1]; low => breakage => cheaper
    benefit = df[["f13", "f14", "f15", "f16"]].sum(axis=1, min_count=1)
    t = pd.DataFrame(index=df.index)
    t["rewards_cost"]   = _rank(df.f21) + REWARDS_LAMBDA * _rank(df.f4) * (1 - redemption_intensity)
    t["perks_cost"]     = _rank(benefit)
    t["servicing_cost"] = df.f2.fillna(0)                          # already ~0/1
    return t.fillna(0.0)


def risk_factor(df: pd.DataFrame) -> pd.Series:
    """[0, cap): PD-like f11 (ranked) amplified by collection calls f3. Shaves the whole score."""
    r = RISK_A * _rank(df.f11) + RISK_B * df.f3.fillna(0)
    return r.fillna(0.0).clip(0, RISK_CAP)


def score(df: pd.DataFrame, weights: dict = WEIGHTS) -> pd.Series:
    """Profitability score per row: (Revenue − Cost) × (1 − Risk), weights keyed by segment."""
    seg = segment(df)
    rev_t, cost_t = revenue_terms(df), cost_terms(df)
    risk = risk_factor(df)
    rev = pd.Series(0.0, index=df.index)
    cost = pd.Series(0.0, index=df.index)
    for si, sname in enumerate(SEGMENTS):
        m = (seg == sname)
        for term in REV_TERMS:
            rev[m] += weights[term][si] * rev_t.loc[m, term]
        for term in COST_TERMS:
            cost[m] += weights[term][si] * cost_t.loc[m, term]
    return (rev - cost) * (1 - risk)


def _self_check():
    """Tiny hand-built frame: covers all 3 segments; a high-spend/low-risk member must outrank a
    tiny-spend/high-risk one; ranges stay comparable; scoring is deterministic."""
    demo = pd.DataFrame({
        "id":  [0, 1, 2, 3],
        "f1":  [0.0, 5000.0, 2000.0, 0.0],          # row1 revolver, row2 lender, row0/3 transactor
        "f2":  [0, 0, 0, 1], "f3": [0, 0, 0, 1],
        "f4":  [100000.0, 50000.0, 80000.0, 200000.0],
        "f5":  [12000.0, 3000.0, 6000.0, 400.0],
        "f6":  [10000.0, 2000.0, 4000.0, 80.0], "f7": [40000.0, 8000.0, 15000.0, 150.0],
        "f8":  [2000.0, 500.0, 900.0, 40.0], "f9": [2000.0, 500.0, 900.0, 40.0],
        "f10": [5000.0, 1000.0, 2000.0, 90.0],
        "f11": [0.01, 0.05, 0.03, 0.30], "f12": [20, 30, 25, 40],
        "f13": [1, 0, 1, 0], "f14": [50, 0, 30, 0], "f15": [5, 3, 4, 0], "f16": [60, 50, 55, 40],
        "f17": [np.nan, np.nan, 30000.0, np.nan], "f18": [np.nan, np.nan, 28000.0, np.nan],
        "f19": [2, 1, 2, 1], "f20": [2, 1, 2, 1], "f21": [80000.0, 10000.0, 40000.0, 5000.0],
        "f22": [5, 4, 4, 3], "f23": [np.nan, np.nan, np.nan, np.nan],
    })
    assert set(segment(demo)) == {"transactor", "revolver", "lender"}, segment(demo).tolist()
    rt, ct = revenue_terms(demo), cost_terms(demo)
    assert rt.notna().all().all() and ct.notna().all().all(), "terms must have no NaN after fill"
    assert (rt.to_numpy() >= 0).all() and (rt.to_numpy() <= 1.001).all(), "rev terms out of [0,1]"
    assert risk_factor(demo).between(0, RISK_CAP).all()
    s = score(demo)
    assert s.notna().all()
    assert s[0] > s[3], f"high-value row0 must outrank low-value row3: {s.round(3).tolist()}"
    assert score(demo).equals(score(demo)), "scoring must be deterministic"
    print("OK score.py self-checks pass:", s.round(3).tolist())


def main():
    _self_check()
    np.random.seed(SEED)
    df = PremierEDA().df
    s = score(df)
    assert s.notna().all(), "scored output has NaNs"
    out = pd.DataFrame({"id": df["id"], "score": s}).sort_values("id")
    OUT.parent.mkdir(exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"scored {len(out):,} rows -> {OUT}")
    print(out.score.describe().round(4))


if __name__ == "__main__":
    main()
