"""Magnitude framework (v2.0 — submission v3+). Rank by ESTIMATED DOLLAR contribution margin,
NOT percentile rank.

Hypothesis (stage-9): the true top-20% is whale-shaped — a few high-dollar members hold most of
the profit. Percentile-ranking every term (framework v1.x) flattens that concentration (our two
percentile submissions both capped ~0.46 on the public LB), so it structurally cannot match a
concentrated truth. This scores each member's profit in (proxy) dollars instead, letting natural
magnitudes weight the features the way an issuer P&L does.

    score_$ = interchange + net_interest − rewards − benefit_credits − expected_loss

Rates are proxy-annualized (masked units treated as proxy-dollars; documented in
framework-doc-v3-magnitude.md). Uses only f1–f23, never id. Deterministic.

Run:  .venv/bin/python src/score_magnitude.py   # self-check, then writes data/scores_v3.csv (+ v4 spend)
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from eda import PremierEDA, SPEND_CATS

SEED = 42
ROOT = Path(__file__).resolve().parent.parent
# --- proxy rates (research-anchored: Amex 10-K / Fed FEDS 2022 / CFPB) ---
R_INTERCHANGE = 0.022   # Amex blended discount rate on spend
R_INTEREST    = 0.08    # net annual interest margin per $ of carried balance (12% yield − loss/opex)
CPP           = 0.010   # issuer cost per redeemed reward point ($)
LGD           = 0.50    # loss-given-default fraction on credit exposure
LOUNGE_COST   = 35.0    # issuer cost per lounge visit ($)


def spend_dollars(df: pd.DataFrame) -> pd.Series:
    """Total spend in proxy dollars on ONE comparable scale across both cohorts.
    Breakdown cohort: uncensored category-sum f6–f10. No-breakdown cohort: f5 is capped (~13.6K)
    and on a different scale, so we QUANTILE-MAP it onto the breakdown spend distribution — this
    preserves each no-breakdown member's internal f5 ordering but lets them compete fairly instead
    of being crushed below everyone by an 18x ceiling artifact (A1). Missing both -> 0.
    Assumes the no-breakdown cohort's spend distribution resembles the breakdown cohort's."""
    cat = df[SPEND_CATS].sum(axis=1, min_count=1)
    out = cat.copy()
    nb = cat.isna() & df.f5.notna()                       # no-breakdown but has total spend
    if nb.any() and cat.notna().any():
        ref = np.sort(cat[cat.notna()].to_numpy())
        f5r = df.loc[nb, "f5"].rank(pct=True).to_numpy()
        out.loc[nb] = np.quantile(ref, f5r)               # f5 percentile -> breakdown $ distribution
    return out.fillna(0.0)


def dollar_profit(df: pd.DataFrame) -> pd.Series:
    """Estimated annual dollar contribution margin = revenue − cost, in proxy dollars."""
    f = df.fillna(0.0)
    sp = spend_dollars(df).values
    interchange = R_INTERCHANGE * sp
    interest    = R_INTEREST * f.f1.values
    rewards     = CPP * f.f21.values
    benefits    = f.f14.values + f.f15.values + f.f16.values + LOUNGE_COST * f.f13.values
    exp_loss    = LGD * f.f11.values * f.f1.values
    return pd.Series(interchange + interest - rewards - benefits - exp_loss, index=df.index)


def dollar_spend(df: pd.DataFrame) -> pd.Series:
    """Benchmark: rank purely by spend dollars (tests 'is the truth just spend magnitude?')."""
    return spend_dollars(df)


# Per-$ NET margins by spend category (interchange minus category-specific reward cost), cited
# from the unit-economics research: airline/lodging are net-NEGATIVE (5x reward cost > discount),
# dining/other/entertainment net-positive. These FOLD IN the spend-driven reward cost.
CAT_MARGIN = {"f6": -0.020, "f7": 0.013, "f8": 0.010, "f9": -0.015, "f10": 0.0185}


def dollar_profit_catmargin(df: pd.DataFrame) -> pd.Series:
    """v5: dollar_profit but interchange is replaced by CATEGORY-MARGIN-weighted spend — each spend
    category earns its own net margin (airline/lodging negative). Since spend dominates the ranking,
    reshaping the spend signal is the highest-leverage lever. Category margins already net per-category
    reward cost, so the flat f21 reward term is dropped. No-breakdown cohort: quantile-mapped spend ×
    the breakdown cohort's realized average net margin (keeps the cohorts on consistent footing)."""
    f = df.fillna(0.0)
    has_bd = df[SPEND_CATS].notna().any(axis=1).values
    catrev = sum(CAT_MARGIN[c] * f[c].values for c in SPEND_CATS)
    sp = spend_dollars(df).values
    blend = catrev[has_bd].sum() / sp[has_bd].sum() if sp[has_bd].sum() else 0.0  # breakdown avg margin
    catrev = np.where(has_bd, catrev, blend * sp)
    benefits = f.f14.values + f.f15.values + f.f16.values + LOUNGE_COST * f.f13.values
    exp_loss = LGD * f.f11.values * f.f1.values
    return pd.Series(catrev + R_INTEREST * f.f1.values - benefits - exp_loss, index=df.index)


CPP_CONTINGENT = CPP * 0.9 * 0.2   # cost/pt × redemption prob × annual expensing fraction


def dollar_profit_catmargin_f4(df: pd.DataFrame) -> pd.Series:
    """v6: v5 category-margin MINUS a small contingent liability on the outstanding points balance f4
    (annualized expected redemption cost). Re-adds a real cost the period-flow versions dropped —
    members sitting on large unredeemed balances carry a future cost."""
    f = df.fillna(0.0)
    return pd.Series(dollar_profit_catmargin(df).values - CPP_CONTINGENT * f.f4.values, index=df.index)


def _self_check():
    """A high-spend, low-risk, low-redemption member must outrank a low-spend, high-reward,
    high-risk one; scoring is deterministic; no NaNs."""
    demo = pd.DataFrame({
        "id": [0, 1, 2],
        "f1": [3000.0, 0.0, 8000.0], "f2": [0, 0, 1], "f3": [0, 0, 1],
        "f4": [50000.0, 5000.0, 300000.0], "f5": [9000.0, 300.0, 2000.0],
        "f6": [20000.0, 200.0, 1000.0], "f7": [60000.0, 400.0, 3000.0], "f8": [5000.0, 50.0, 200.0],
        "f9": [8000.0, 50.0, 300.0], "f10": [12000.0, 100.0, 500.0],
        "f11": [0.01, 0.02, 0.30], "f12": [10, 5, 2],
        "f13": [1, 0, 12], "f14": [0.0, 0.0, 200.0], "f15": [0.0, 0.0, 50.0], "f16": [10.0, 0.0, 64.0],
        "f17": [np.nan, np.nan, 40000.0], "f18": [np.nan, np.nan, 38000.0],
        "f19": [1, 1, 3], "f20": [2, 1, 2], "f21": [5000.0, 1000.0, 350000.0],
        "f22": [3, 2, 1], "f23": [1, 1, 0],
    })
    p = dollar_profit(demo)
    assert p.notna().all(), p
    assert p[0] > p[1] > p[2], f"profitable order broken: {p.round(1).tolist()}"  # row2 = unprofitable maximizer
    assert dollar_profit(demo).equals(dollar_profit(demo)), "must be deterministic"
    print("OK score_magnitude.py self-check:", p.round(1).tolist())


def main():
    _self_check()
    np.random.seed(SEED)
    df = PremierEDA().df
    for name, fn in [("scores_v3", dollar_profit), ("scores_v4", dollar_spend),
                     ("scores_v5", dollar_profit_catmargin), ("scores_v6", dollar_profit_catmargin_f4)]:
        s = fn(df)
        assert s.notna().all(), f"{name} has NaNs"
        out = pd.DataFrame({"id": df["id"], "score": s}).sort_values("id")
        (ROOT / "data").mkdir(exist_ok=True)
        out.to_csv(ROOT / "data" / f"{name}.csv", index=False)
        print(f"\n{name}:  range [{s.min():.1f}, {s.max():.1f}]  distinct {s.nunique():,}")
        print(s.describe().round(2).to_string())


if __name__ == "__main__":
    main()
