"""Per-weight sensitivity for the v1 score — which weights actually decide the top-20%.

No profit label exists, so weights cannot be fit to truth. Stage-6 calibration is therefore:
(1) confirm the business-prior weights are robust (not knife-edge), and (2) find the high-leverage
terms so they get the strongest business justification and the most care. Leaderboard-informed
numeric tuning waits until submission #1 returns feedback — grid-searching now fits nothing real.

For each term we drop it (weight x0) and nudge it (x0.75 / x1.25) and measure how much the top-20%
membership moves (1 - Jaccard vs the baseline top-20%). Large move = load-bearing term.

Run:  .venv/bin/python src/calibrate.py
"""
from __future__ import annotations
import copy
import numpy as np
import pandas as pd
from eda import PremierEDA
from score import score, WEIGHTS, REV_TERMS, COST_TERMS
from validation import top_set, jaccard

ALL_TERMS = list(REV_TERMS) + list(COST_TERMS)


def scaled_weights(term: str, factor: float) -> dict:
    """A copy of WEIGHTS with one term's weight scaled across all three segments."""
    w = copy.deepcopy(WEIGHTS)
    w[term] = tuple(x * factor for x in w[term])
    return w


def leverage(df: pd.DataFrame) -> pd.DataFrame:
    """Top-20% churn (1 - Jaccard vs base) when each term's weight is dropped / nudged +/-25%."""
    base_top = top_set(score(df))
    rows = []
    for t in ALL_TERMS:
        drop = 1 - jaccard(base_top, top_set(score(df, scaled_weights(t, 0.0))))
        up   = 1 - jaccard(base_top, top_set(score(df, scaled_weights(t, 1.25))))
        dn   = 1 - jaccard(base_top, top_set(score(df, scaled_weights(t, 0.75))))
        rows.append({"term": t, "drop_churn": round(drop, 3), "jitter25_churn": round(max(up, dn), 3)})
    return pd.DataFrame(rows).set_index("term").sort_values("drop_churn", ascending=False)


def main():
    df = PremierEDA().df
    print("Per-term weight leverage on the top-20% (higher = more load-bearing):\n")
    print(leverage(df))
    print("\nread: drop_churn     = fraction of the top-20% that changes if the term is removed entirely")
    print("      jitter25_churn  = fraction that changes under a +/-25% weight nudge")
    print("      high drop + low jitter = important AND robust (ideal); ~0 drop = term barely matters (candidate to cut);")
    print("      high jitter = knife-edge -> justify carefully and revisit after the first leaderboard signal")


if __name__ == "__main__":
    # self-check on a tiny frame: scaling works; identity has no churn; churn stays in [0,1]
    assert scaled_weights("spending", 0.0)["spending"] == (0.0, 0.0, 0.0)
    rng = np.random.default_rng(0)
    demo = pd.DataFrame(rng.integers(0, 100, size=(50, 23)).astype(float), columns=[f"f{i}" for i in range(1, 24)])
    demo.insert(0, "id", range(50))
    assert jaccard(top_set(score(demo)), top_set(score(demo))) == 1.0
    lv = leverage(demo)
    assert lv["drop_churn"].between(0, 1).all() and lv["jitter25_churn"].between(0, 1).all(), lv
    print("OK calibrate.py self-checks pass\n")
    main()
