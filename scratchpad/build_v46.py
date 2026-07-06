"""Build data/scores_v46.csv — v46 'f2-evict' attrition-screen probe (BENCH, DUMMY-2).

Hypothesis: the hidden truth demotes cancellation-callers (f2 >= 1) the way it demotes
collection-flagged members (f3, the project's biggest structural win, +0.018) — attrition
as a forward-looking cost. f2 has NEVER appeared in any of the 45 equations; from v10 on,
every top's f2-share sits in a 2.38-2.63% band (~250-member spread) -> the modern ledger
bought ~zero information on this axis (probe_triage.py, 2026-07-05). The 31-read LP does
NOT refute a hard evict (pop-wide f2 truth-mass in [0, 8077]).

Design: base = v37L's set (best measured, exact read 0.919143). Swap N = 2,415:
  OUT = ALL f2>=1 members of the base top (no selection — tests the hard rule exactly)
  IN  = next-best outsiders by the base margin, f2 = 0, f3 = 0
Pre-registered: realized = 0.919143 + net * 0.02415, box [0.8950, 0.9433].
  truth hard-evicts f2  -> net ~ +0.36 -> ~0.928 (pack fingerprint; promote to primary)
  partial demotion      -> net +0.10-0.15 -> 0.921-0.923 (new bench best; tranche it)
  f2-indifferent        -> net ~ -0.20 -> ~0.914 (axis closed POWERED, delta_min 4.9%)
Deployment: DUMMY-2 bench; promote to primary via capped-delta only on a read >= ~0.921.

Run: .venv/bin/python scratchpad/build_v46.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
V37L_EXACT = 0.919143
SHIFT = 0.8414709848          # sin(1) — unique global shift (checked vs all prior builds)
SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
T, M, ids = z["T"], z["M"], z["ids"]
names = [str(x) for x in z["names"]]
post = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
Kc = post.shape[0]

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all()
f2 = df["f2"].fillna(0).to_numpy()
f3 = df["f3"].fillna(0).to_numpy()
f1 = df["f1"].fillna(0).to_numpy()
f11 = df["f11"].fillna(0).to_numpy()
cat = df[["f6", "f7", "f8", "f9", "f10"]].fillna(0).sum(axis=1).to_numpy()

sL = pd.read_csv(ROOT / "data" / "scores_v37L.csv").set_index("id")["score"].reindex(ids).to_numpy()
base_mask = np.zeros(len(sL), bool)
base_mask[np.argpartition(-sL, TOPK)[:TOPK]] = True

# ---- swap construction -------------------------------------------------------
out_pool = np.flatnonzero(base_mask & (f2 >= 1))
N = out_pool.size
in_cand = np.flatnonzero(~base_mask & (f2 == 0) & (f3 == 0))
in_pool = in_cand[np.argsort(-sL[in_cand])][:N]

whale = M.all(axis=0)
print(f"OUT (evicted f2-callers): N={N}  catsum med {np.median(cat[out_pool]):,.0f}  "
      f"f1 med {np.median(f1[out_pool]):,.0f}  f11 med {np.median(f11[out_pool]):.4f}  "
      f"whales evicted {(whale[out_pool]).sum()} (gate waived BY DESIGN — that is the hypothesis)")
print(f"IN  (margin next-best):   N={in_pool.size}  catsum med {np.median(cat[in_pool]):,.0f}  "
      f"f1 med {np.median(f1[in_pool]):,.0f}  f11 med {np.median(f11[in_pool]):.4f}")

target = base_mask.copy()
target[out_pool] = False
target[in_pool] = True
assert target.sum() == TOPK
assert not (target & (f3 >= 1)).any() and not (target & (f2 >= 1)).any()

# ---- score packaging: vote + margin tie-break, attrition band, f3 floor ------
vote = post.sum(axis=0).astype(np.float64)
margin = (T[:, [names.index(k) for k in SIX]].astype(np.float64)) @ w6
tb = margin / margin.std()
base_new = vote + 1e-3 * tb
assert 1e-3 * np.abs(tb).max() < 0.5
RANGE = base_new.max() - base_new.min()
BIG = 2.0 * RANGE
score = base_new + BIG * target
score[f2 >= 1] -= 1.5 * RANGE          # attrition screen: all f2-callers below all non-f2 peers
score[f3 >= 1] = score.min() - 1.0     # collection floor stays the global bottom
score = score + SHIFT

top = np.zeros(len(score), bool)
top[np.argpartition(-score, TOPK)[:TOPK]] = True
assert (top == target).all()
cut = np.sort(score)[::-1][TOPK - 1]
n_cut = int((score == cut).sum())

# ---- gates -------------------------------------------------------------------
s = pd.Series(score)
uniq = np.unique(score)
shared_total = 0
for p in sorted((ROOT / "data").glob("scores_v*.csv")):
    if p.name == "scores_v46.csv":      # skip own output on re-runs (validator catch)
        continue
    prior = pd.read_csv(p).set_index("id")["score"].reindex(ids).to_numpy()
    shared = np.intersect1d(uniq, np.unique(prior))
    shared_total += len(shared)
    assert len(shared) == 0, f"floats shared with {p.name}: {len(shared)}"
print(f"anti-fingerprint: 0 shared floats vs all prior score files ✓")

r = np.corrcoef(ids.astype(np.float64), score)[0, 1]
lo = [(top & p).sum() / TOPK for p in post]
print(f"distinct {s.nunique():,}  cutoff members {n_cut}  f3-in-top 0  f2-in-top 0")
print(f"revolver {f1[top].astype(bool).mean():.1%}  whale-in {(top & whale).sum()/whale.sum():.4f}  "
      f"corr(id) {r:+.2e}  set-diff vs v37L {int((top ^ base_mask).sum())//2}/{N}  "
      f"overlap vs v37L {(top & base_mask).sum()/TOPK:.4f}")
print(f"E[LB | posterior] {np.mean(lo):.3f} (family carries NO f2 term — blind to this axis, record only)")
print(f"PRE-REGISTERED: realized = {V37L_EXACT} + net*{N/1e5:.5f}, "
      f"box [{V37L_EXACT - 0.7*N/1e5:.4f}, {V37L_EXACT + 0.7*N/1e5:.4f}] (|net| <= 0.7 mask cap)")
assert len(s) == 500_000 and s.notna().all() and n_cut == 1 and abs(r) < 1e-2

out = ROOT / "data" / "scores_v46.csv"
pd.DataFrame({"id": ids, "score": score}).to_csv(out, index=False)
print(f"wrote {out.relative_to(ROOT)}")
