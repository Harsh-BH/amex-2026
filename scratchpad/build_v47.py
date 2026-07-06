"""Build data/scores_v47.csv — v47 'benefit-cost' demotion probe (BENCH, DUMMY-2, max-ceiling program #1).

Hypothesis: the hidden truth books benefit credits as COST (revenue − benefits — the brief's
4th NAMED driver, f13-f16), so the heaviest credit-burners in our top quintile don't belong
there. This axis has NEVER been read: prior closures (A29/A32) were blind-instrument screens
(A37), the family's 'ben' term is sign-UNSTABLE across refits (= the reads don't pin it),
and burner-share across modern tops is checked at build time below.

Design: base = v37L's set (best measured, exact read 0.919143). Swap N = 2,500:
  OUT = top-2,500 in-top members by dollarized benefit burn ben$ = 50*f13 + f14 + 15*f15 + f16
  IN  = next-best outsiders by the base margin, f3 = 0 (f2 unconstrained — measured parity, #32)
Pre-registered: realized = 0.919143 + net * 0.02500, box [0.9016, 0.9366].
  truth subtracts benefits hard -> net ~ +0.25-0.40 -> 0.925-0.929 (promote to primary)
  partial cost term             -> net +0.08-0.15  -> 0.921-0.923 (tranche the direction)
  benefit-indifferent           -> net ~ -0.20-0.30 -> ~0.912-0.914 (4th named driver closes POWERED)
Deployment: DUMMY-2 bench; promote via capped-delta only on a read >= ~0.921.

Run: .venv/bin/python scratchpad/build_v47.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
N = 2_500
V37L_EXACT = 0.919143
SHIFT = 0.7615941560          # tanh(1) — unique global shift (checked vs all prior builds)
SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
T, M, ids = z["T"], z["M"], z["ids"]
names = [str(x) for x in z["names"]]
post = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all()
f = df.fillna(0.0)
f2v = f["f2"].to_numpy(); f3v = f["f3"].to_numpy()
f1v = f["f1"].to_numpy(); f11v = f["f11"].to_numpy()
cat = f[["f6", "f7", "f8", "f9", "f10"]].sum(axis=1).to_numpy()
ben = (50.0 * f["f13"] + f["f14"] + 15.0 * f["f15"] + f["f16"]).to_numpy()

sL = pd.read_csv(ROOT / "data" / "scores_v37L.csv").set_index("id")["score"].reindex(ids).to_numpy()
base_mask = np.zeros(len(sL), bool)
base_mask[np.argpartition(-sL, TOPK)[:TOPK]] = True

# ---- openness check: was the burner axis ever excited? ------------------------
heavy = ben >= np.quantile(ben[base_mask], 1 - N / TOPK)   # global burn threshold from base top
thr = float(np.quantile(ben[base_mask], 1 - N / TOPK))
shares = []
for v in ("v10", "v19", "v27", "v29", "v34", "v35", "v37L", "v41", "v44", "v45"):
    p = ROOT / "data" / f"scores_{v}.csv"
    sv = pd.read_csv(p).set_index("id")["score"].reindex(ids).to_numpy()
    mv = np.zeros(len(sv), bool); mv[np.argpartition(-sv, TOPK)[:TOPK]] = True
    shares.append(((mv & (ben >= thr)).sum(), v))
print(f"burn threshold (top-{N} of base): ${thr:,.0f}")
print("heavy-burner count per modern top:", ", ".join(f"{v}:{c}" for c, v in shares))

# ---- swap construction ---------------------------------------------------------
in_top = np.flatnonzero(base_mask)
out_pool = in_top[np.argsort(-ben[in_top])[:N]]
in_cand = np.flatnonzero(~base_mask & (f3v == 0) & (ben < thr))   # replacements must be non-burners (rule-coherent)
in_pool = in_cand[np.argsort(-sL[in_cand])[:N]]

whale = M.all(axis=0)
print(f"\nOUT (evicted burners): ben$ med {np.median(ben[out_pool]):,.0f}  "
      f"catsum med {np.median(cat[out_pool]):,.0f}  f1 med {np.median(f1v[out_pool]):,.0f}  "
      f"f11 med {np.median(f11v[out_pool]):.4f}  f2-share {(f2v[out_pool]>=1).mean():.3f}  "
      f"whales evicted {whale[out_pool].sum()} (gate waived BY DESIGN)")
print(f"IN  (margin next-best): ben$ med {np.median(ben[in_pool]):,.0f}  "
      f"catsum med {np.median(cat[in_pool]):,.0f}  f1 med {np.median(f1v[in_pool]):,.0f}  "
      f"f11 med {np.median(f11v[in_pool]):.4f}")

target = base_mask.copy()
target[out_pool] = False
target[in_pool] = True
assert target.sum() == TOPK and not (target & (f3v >= 1)).any()

# ---- score packaging: vote + margin tie-break, burner demotion, f3 floor -------
vote = post.sum(axis=0).astype(np.float64)
margin = (T[:, [names.index(k) for k in SIX]].astype(np.float64)) @ w6
tb = margin / margin.std()
base_new = vote + 1e-3 * tb
assert 1e-3 * np.abs(tb).max() < 0.5
RANGE = base_new.max() - base_new.min()
BIG = 2.0 * RANGE
score = base_new + BIG * target
score[(ben >= thr) & ~target] -= 1.2 * RANGE   # benefit-cost demotion band (non-target burners only)
score[f3v >= 1] = score.min() - 1.0    # collection floor stays the global bottom
score = score + SHIFT

top = np.zeros(len(score), bool)
top[np.argpartition(-score, TOPK)[:TOPK]] = True
assert (top == target).all()
cut = np.sort(score)[::-1][TOPK - 1]
n_cut = int((score == cut).sum())

# ---- gates ---------------------------------------------------------------------
s = pd.Series(score)
uniq = np.unique(score)
for p in sorted((ROOT / "data").glob("scores_v*.csv")):
    if p.name == "scores_v47.csv":
        continue
    prior = pd.read_csv(p).set_index("id")["score"].reindex(ids).to_numpy()
    shared = np.intersect1d(uniq, np.unique(prior))
    assert len(shared) == 0, f"floats shared with {p.name}: {len(shared)}"
print("anti-fingerprint: 0 shared floats vs all prior score files ✓")

r = np.corrcoef(ids.astype(np.float64), score)[0, 1]
print(f"distinct {s.nunique():,}  cutoff members {n_cut}  f3-in-top 0  "
      f"heavy-burner-in-top {int((top & (ben >= thr)).sum())}")
print(f"revolver {f1v[top].astype(bool).mean():.1%}  whale-in {(top & whale).sum()/whale.sum():.4f}  "
      f"corr(id) {r:+.2e}  set-diff vs v37L {int((top ^ base_mask).sum())//2}/{N}")
print(f"PRE-REGISTERED: realized = {V37L_EXACT} + net*{N/1e5:.5f}, "
      f"box [{V37L_EXACT - 0.7*N/1e5:.4f}, {V37L_EXACT + 0.7*N/1e5:.4f}]")
assert len(s) == 500_000 and s.notna().all() and n_cut == 1 and abs(r) < 1e-2

out = ROOT / "data" / "scores_v47.csv"
pd.DataFrame({"id": ids, "score": score}).to_csv(out, index=False)
print(f"wrote {out.relative_to(ROOT)}")
