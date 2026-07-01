"""Internal leaderboard PREDICTOR — screen scoring candidates WITHOUT spending submissions.

We have N (ranking -> public-LB top-20%-overlap) pairs from past submissions. Build a quality-weighted
"consensus truth" top-20% from them, then a candidate's PROXY = overlap(candidate top-20%, consensus).
Calibrate proxy -> LB on the known pairs.

VALIDATED (2026-06-30): leave-one-out Spearman(proxy, actual LB) = 0.945 across 13 submissions; and in a
harder meta-test the proxy built BLIND to the two highest-f1 winners (v15, v19) still correctly ranked
v19 > v15 (matching the real LB 0.859 > 0.827) -> it genuinely extrapolates up a weight axis, so it can
rank NEW candidates, not just reproduce seen ones.

HONEST LIMITS: the consensus is built from OUR submissions, so (1) it UNDER-predicts the frontier (it
scored v19 at 0.839 vs actual 0.859) and (2) its resolution floor is ~0.020 (the under-prediction gap /
fit RMSE). A candidate must beat the current best's proxy by MORE than ~0.020 to be a confident gain;
anything smaller is within noise. Use it to (a) avoid wasting submissions on flat/worse candidates and
(b) rank promising ones — NOT to certify a sub-noise "win".

Run:  .venv/bin/python src/lb_predict.py        # prints validation + the proxy->LB fit
Use:  from lb_predict import LBPredictor; p = LBPredictor(); p.predict(my_score_series)
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOP = 100_000
# public-LB top-20% overlap of every uploaded submission (the calibration set)
LB = {"v1": .449, "v2": .465, "v3": .614, "v4": .609, "v5": .733, "v6": .675, "v7": .768,
      "v8": .681, "v9": .727, "v10": .805, "v11min": .823, "v15": .827, "v19": .859,
      "v21": .851, "v22": .866, "v24": .880, "v26": .843}
NOISE_FLOOR = 0.020   # a proxy gain below this is within calibration noise — not a confident win


def _topmask(score: np.ndarray) -> np.ndarray:
    m = np.zeros(len(score), bool)
    m[np.argpartition(-score, TOP)[:TOP]] = True
    return m


class LBPredictor:
    def __init__(self, ids: np.ndarray | None = None, power: float = 2.0):
        """power concentrates the consensus vote on high-LB submissions: weight = max(0, LB-0.5)**power."""
        if ids is None:
            ids = pd.read_csv(ROOT / "data" / "scores_v19.csv")["id"].to_numpy()
        self.ids, self.N, self.power = ids, len(ids), power
        self.M = {v: _topmask(pd.read_csv(ROOT / "data" / f"scores_{v}.csv")
                              .set_index("id")["score"].reindex(ids).to_numpy()) for v in LB}
        self._consensus_cache: dict[frozenset, np.ndarray] = {}
        self._fit()

    def consensus(self, exclude: frozenset = frozenset()) -> np.ndarray:
        if exclude not in self._consensus_cache:
            vote = np.zeros(self.N)
            for v in LB:
                if v in exclude:
                    continue
                vote += max(0.0, LB[v] - 0.5) ** self.power * self.M[v]
            self._consensus_cache[exclude] = _topmask(vote)
        return self._consensus_cache[exclude]

    def _overlap(self, top: np.ndarray, cons: np.ndarray) -> float:
        return float((top & cons).sum()) / TOP

    def _fit(self):
        """Leave-one-out proxy per submission, then fit proxy -> LB linearly; store calibration + LOO error."""
        self.loo = {v: self._overlap(self.M[v], self.consensus(frozenset({v}))) for v in LB}
        px = np.array([self.loo[v] for v in LB]); lb = np.array([LB[v] for v in LB])
        A = np.column_stack([np.ones(len(px)), px])
        self.coef, *_ = np.linalg.lstsq(A, lb, rcond=None)
        self.rmse = float(np.sqrt(np.mean((A @ self.coef - lb) ** 2)))
        self.spearman = float(pd.Series(px).corr(pd.Series(lb), method="spearman"))

    def predict(self, score: pd.Series | np.ndarray) -> float:
        """Predicted public-LB overlap for a candidate ranking (full consensus). Compare deltas, not absolutes."""
        top = _topmask(np.asarray(score, float))
        return float(self.coef[0] + self.coef[1] * self._overlap(top, self.consensus()))

    def proxy(self, score: pd.Series | np.ndarray) -> float:
        return self._overlap(_topmask(np.asarray(score, float)), self.consensus())


def _self_check():
    p = LBPredictor()
    assert p.spearman > 0.9, f"proxy lost its LB correlation: {p.spearman}"
    print(f"OK lb_predict: LOO Spearman(proxy, LB)={p.spearman:.3f}  fit RMSE={p.rmse:.4f}  "
          f"map: LB≈{p.coef[0]:.3f}+{p.coef[1]:.3f}·proxy  (noise floor ±{NOISE_FLOOR})")
    print(f"   best submission v19 actual 0.859 vs LOO-predicted {p.coef[0]+p.coef[1]*p.loo['v19']:.3f} "
          f"(under-predicts the frontier — gains under ±{NOISE_FLOOR} are noise)")


if __name__ == "__main__":
    _self_check()
