"""Compare the v1 score against transparent baseline rankers (no ground truth exists).

No profit label exists, so "is our ranking correct?" cannot be answered locally. This measures
AGREEMENT between our score and independently-motivated rankers: convergence = confidence,
divergence (especially in the top-20%) = where our design choices bite or what to investigate.
Headline metric = top-20% overlap % — the SAME metric the competition grades on — applied
between rankings instead of against the hidden truth. Also reports Spearman rank correlation.

Run:  .venv/bin/python src/compare.py
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from eda import PremierEDA, SPEND_CATS, FEATS
from score import score, revenue_terms, cost_terms, risk_factor, REV_TERMS, COST_TERMS
from validation import top_set

# P&L sign per feature for the objective-weighting baseline (from .claude/memory/feature-notes.md roles).
# +1 revenue/value, -1 cost/risk, 0 ambiguous engagement (excluded).
PNL_SIGN = {
    "f1": +1, "f5": +1, "f6": +1, "f7": +1, "f8": +1, "f9": +1, "f10": +1,
    "f17": +1, "f18": +1, "f19": +1, "f20": +1,
    "f2": -1, "f3": -1, "f4": -1, "f11": -1, "f13": -1, "f14": -1, "f15": -1, "f16": -1, "f21": -1,
    "f12": 0, "f22": 0, "f23": 0,
}


def _r(s: pd.Series) -> pd.Series:
    return s.rank(pct=True)


def baselines(df: pd.DataFrame) -> dict:
    """Independent alternative rankings of all 500K (higher = more profitable). No NaN (missing -> 0)."""
    out = {}
    out["f5_only"]   = _r(df.f5)                                      # naive single-feature 'total spend'
    out["spend_sum"] = _r(df[SPEND_CATS].sum(axis=1, min_count=1))    # revenue volume only, no cost/risk
    # objective MCDA: sign-oriented, CRITIC-weighted composite of all features ('let the math weight it')
    R = df[FEATS].rank(pct=True).fillna(0.5)
    crit = R.std() * (1 - R.corr().abs()).sum()
    w = crit / crit.sum()
    out["objective_critic"] = R.mul([PNL_SIGN[c] * w[c] for c in FEATS], axis=1).sum(axis=1)
    # our exact terms, equal-weighted, NO per-segment tilt (isolates the value of the segment weighting)
    rev_t, cost_t = revenue_terms(df), cost_terms(df)
    out["equal_weight_flat"] = (rev_t[list(REV_TERMS)].mean(axis=1)
                                - cost_t[list(COST_TERMS)].mean(axis=1)) * (1 - risk_factor(df))
    return {k: v.fillna(0.0) for k, v in out.items()}


def overlap_pct(a: set, b: set) -> float:
    """% of the top-20% sets that coincide (equal-size sets => the competition's metric form)."""
    return len(a & b) / len(a) if a else float("nan")


def spearman(x: pd.Series, y: pd.Series) -> float:
    """Spearman rho = Pearson correlation of the ranks. No scipy needed."""
    return float(np.corrcoef(x.rank(), y.rank())[0, 1])


def compare(df: pd.DataFrame) -> pd.DataFrame:
    """Agreement of each baseline with the v1 score: top-20% overlap % + Spearman rho."""
    ours = score(df)
    our_top = top_set(ours)
    rows = [{"baseline": name,
             "top20_overlap%": round(100 * overlap_pct(our_top, top_set(b)), 1),
             "spearman_rho": round(spearman(ours, b), 3)}
            for name, b in baselines(df).items()]
    return pd.DataFrame(rows).set_index("baseline")


def main():
    out = compare(PremierEDA().df)
    print("v1 score vs baseline rankers — AGREEMENT, not ground truth:\n")
    print(out)
    print("\nread: low  f5_only          overlap => our score departs from naive spend (expected; f5 is saturated)")
    print("      high equal_weight_flat overlap => per-segment weighting changes few of the top-20%")
    print("      objective_critic            => the label-free 'let the math weight it' approach we rejected")


if __name__ == "__main__":
    # self-check: the comparison machinery is correct on a tiny deterministic frame
    assert overlap_pct({1, 2, 3}, {1, 2, 3}) == 1.0
    assert overlap_pct({1, 2, 3}, {4, 5, 6}) == 0.0
    rng = np.random.default_rng(0)
    demo = pd.DataFrame(rng.integers(0, 100, size=(40, len(FEATS))).astype(float), columns=FEATS)
    demo.insert(0, "id", range(40))
    assert abs(spearman(demo.f5, demo.f5) - 1.0) < 1e-9
    out = compare(demo)
    assert out["top20_overlap%"].between(0, 100).all(), out
    assert out["spearman_rho"].between(-1, 1).all(), out
    print("OK compare.py self-checks pass\n")
    main()
