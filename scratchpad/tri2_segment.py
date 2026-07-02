"""Two-regime (segment-conditional) family test — the last big structural hypothesis.

Hypothesis: the truth uses different rates for lend-line holders (f17 present, 41.5% of pop)
vs charge-only members — e.g. Pay-Over-Time fee/interest lines that only exist for one cohort.
Our family has always been ONE global formula; a two-regime truth is outside its span.

Judge ONLY by frontier leave-one-out (in-sample is at the measurement-noise floor and cannot
validate added flexibility). Baseline to beat: 15-term CORE frontier LOO mean|err| = 0.0066.

Run: cd scratchpad && ../.venv/bin/python tri2_segment.py
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triangulate2 as t2

T, M, ids, names, keys = t2.load()
df = pd.read_pickle(t2.ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
lend = (~df["f17"].isna()).to_numpy().astype(np.float32)          # 41.5% lend-line cohort
print(f"lend cohort share: {lend.mean():.3f}")

# extended matrix: CORE terms + (CORE x lend-flag) interactions + the flag itself
core_idx = [names.index(k) for k in t2.CORE]
Tc = T[:, core_idx]
Tx = (Tc * lend[:, None]).astype(np.float32)
flag = t2._scale(lend)
T_ext = np.ascontiguousarray(np.hstack([Tc, Tx, flag[:, None]]))
names_ext = t2.CORE + [f"L*{k}" for k in t2.CORE] + ["lendflag"]

# monkey-patch a fit over the extended matrix (reuse t2.fit machinery via _CTX directly)
from scipy.optimize import differential_evolution

def fit_ext(fit_keys, seed=42, maxiter=150, popsize=96):
    rows = [keys.index(k) for k in fit_keys]
    t2._CTX["T"] = T_ext
    t2._CTX["M"] = np.ascontiguousarray(M[rows])
    obs = np.array([t2.OBS[k] for k in fit_keys])
    t2._CTX["obs"] = obs
    cw = (obs / obs.max()) ** t2.OBS_POW
    t2._CTX["cw"] = cw * len(cw) / cw.sum()
    rng = np.random.default_rng(seed)
    # seeds: global-core solutions with zero interactions, plus jitter
    base = [w for w in t2._dirs(names)]
    init = []
    for w in base:
        v = np.zeros(31); v[:15] = w[core_idx] if len(w) == len(names) else 0
        init.append(v / (np.linalg.norm(v) + 1e-9))
    while len(init) < popsize:
        v = init[rng.integers(len(init))] + 0.2 * rng.standard_normal(31)
        init.append(v)
    res = differential_evolution(t2._loss_vec, [(-3, 3)] * 31, init=np.clip(np.array(init), -2.9, 2.9),
                                 mutation=(0.4, 1.2), recombination=0.85, tol=1e-12, polish=False,
                                 seed=seed, maxiter=maxiter, vectorized=True, updating="deferred")
    return res.x / np.linalg.norm(res.x)

def implied_ext(w, want):
    score = T_ext @ w.astype(np.float32)
    tidx = np.argpartition(-score, t2.TOPK)[:t2.TOPK]
    return {k: M[keys.index(k), tidx].sum() / t2.TOPK for k in want}

HOLD = ["v19", "v21", "v22", "v24", "v26", "v27", "v29", "v30"]
errs = []
for held in HOLD:
    tr = [k for k in keys if k != held]
    w = fit_ext(tr, maxiter=130, popsize=80)
    p = implied_ext(w, [held])[held]
    errs.append(abs(p - t2.OBS[held]))
    print(f"  hold {held:>4}: pred {p:.3f} actual {t2.OBS[held]:.3f} |err| {errs[-1]:.3f}", flush=True)
print(f"TWO-REGIME frontier LOO mean|err| {np.mean(errs):.4f}   (15-term baseline: 0.0066)")

w_full = fit_ext(keys, maxiter=170, popsize=96)
imp = implied_ext(w_full, keys)
rmse = float(np.sqrt(np.mean([(imp[k] - t2.OBS[k]) ** 2 for k in keys])))
big = {n: round(float(x), 3) for n, x in zip(names_ext, w_full) if abs(x) > 0.06}
print(f"full fit RMSE {rmse:.4f}; material weights: {big}")
np.save(t2.ROOT / "scratchpad" / "tri2_segment_w.npy", w_full)
