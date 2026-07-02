"""Whale-safety + composition check for the Triangulation-2.0 candidates.
Whales = members in EVERY historical version's top-20% (n~15.6K, the consensus core).
Every historical LB loss (v6/v8/v26) demoted whales or overshot revolver share; any
candidate we submit must keep whale in-rate ~0.99+ and revolver share in the winning band.
Run after `posterior`: .venv/bin/python scratchpad/tri2_whalecheck.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
T, M, ids = z["T"], z["M"], z["ids"]
names = [str(x) for x in z["names"]]
keys = [str(x) for x in z["obs_keys"]]
CORE = names[:15]

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
f1 = df["f1"].fillna(0).to_numpy()
f3 = df["f3"].fillna(0).to_numpy()
whale = M.all(axis=0)                       # in every submitted top-20%
print(f"whale set (in all 18 submitted tops): {whale.sum():,}")

def mask_of(score):
    m = np.zeros(len(score), bool)
    m[np.argpartition(-np.asarray(score, np.float64), TOPK)[:TOPK]] = True
    return m

def audit(name, m):
    print(f"  {name:<22} whale-in {(m & whale).sum()/whale.sum():.3f}  revolver% {f1[m].astype(bool).mean():.1%}"
          f"  f3-in-top {int((m & (f3==1)).sum()):,}  vs v24 {(m & M[keys.index('v24')]).sum()/TOPK:.3f}")

audit("v24 (anchor)", M[keys.index("v24")])
w = np.load(ROOT / "scratchpad" / "tri2_core_w.npy")
audit("best-fit truth g^", mask_of(T[:, [names.index(k) for k in CORE]] @ w.astype(np.float32)))
p6 = ROOT / "scratchpad" / "tri2_fit6_scores.csv"
if p6.exists():
    s6 = pd.read_csv(p6).set_index("id")["score"].reindex(ids).to_numpy()
    m6 = mask_of(s6)
    audit("fit6 P&L (v27 cand)", m6)
    post = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
    ov = [(m6 & p).sum() / TOPK for p in post]
    print(f"  fit6 E[LB|posterior] {np.mean(ov):.3f}  min {np.min(ov):.3f}  max {np.max(ov):.3f}")
cons = pd.read_csv(ROOT / "scratchpad" / "tri2_consensus_scores.csv").set_index("id")["score"].reindex(ids).to_numpy()
audit("posterior consensus", mask_of(cons))
s22 = pd.read_csv(ROOT / "data" / "scores_v22.csv").set_index("id")["score"].reindex(ids).to_numpy()
s24 = pd.read_csv(ROOT / "data" / "scores_v24.csv").set_index("id")["score"].reindex(ids).to_numpy()
audit("v24 lambda=0.30", mask_of(s22 + 1.5 * (s24 - s22)))
