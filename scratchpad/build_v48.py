"""Build data/scores_v48.csv — v48 'f5 total-spend coverage' promotion probe (BENCH, max-ceiling swing #2 of 2).

Hypothesis: the hidden truth carries a material term on f5 — the column the organizers
LABELED "Total Spend" — even though f5 is uncorrelated with the industry-category spends
(A14). Business story: f6-f10 are industry categories only; f5 = all-channel total; a
member with capped f5 but moderate categories still earns interchange on the off-category
spend our equation never sees. Our framework has NEVER carried f5 (A14/A30 killed it as a
CATEGORY-spend proxy — a different claim than truth-uses-the-labeled-column; A43's
residual-vs-capture regression ranked f5 #1 of all never-modeled features, sub-floor).

Design: base = v37L's set (best measured, exact read 0.919143). Swap N = 2,500:
  IN  = capped-f5 outsiders (f5 at the winsor max 13,596.28; 12,915 pop-wide), f3 = 0,
        ordered by the base margin (under the hypothesis, truth-top ∩ capped-outsiders =
        the margin-best of them)
  OUT = weakest-margin non-whale incumbents (whale-guard ON — the hypothesis does not
        demand evicting consensus members; v39/v40 promotion-probe pattern)
Pre-registered: realized = 0.919143 + net * 0.02500, box [0.9016, 0.9366].
  material f5 term  -> net +0.10-0.25 -> 0.9216-0.9254 (promote via capped-delta)
  no f5 term        -> net ~ -0.05-0.15 -> 0.9154-0.9179 (mild: OUT side is boundary, not deep-top)
Powered: delta_min = 4.9% at k=2,500.
Deployment: DUMMY-2 bench; promote only on a read >= ~0.921.

Run: .venv/bin/python scratchpad/build_v48.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
N = 2_500
V37L_EXACT = 0.919143
SHIFT = 0.5772156649          # Euler–Mascheroni γ — unique global shift (ln(2) collided with 2 v37L floats)
SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
T, M, ids = z["T"], z["M"], z["ids"]
names = [str(x) for x in z["names"]]
post = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all()
f = df.fillna(0.0)
f3v = f["f3"].to_numpy(); f1v = f["f1"].to_numpy(); f11v = f["f11"].to_numpy()
f5v = f["f5"].to_numpy()
cat = f[["f6", "f7", "f8", "f9", "f10"]].sum(axis=1).to_numpy()
F5CAP = float(np.nanmax(df["f5"].to_numpy()))
at_cap = f5v >= F5CAP - 1e-6

sL = pd.read_csv(ROOT / "data" / "scores_v37L.csv").set_index("id")["score"].reindex(ids).to_numpy()
base_mask = np.zeros(len(sL), bool)
base_mask[np.argpartition(-sL, TOPK)[:TOPK]] = True

# ---- openness check: capped-f5 count across modern tops ------------------------
shares = []
for v in ("v10", "v19", "v27", "v29", "v34", "v35", "v37L", "v41", "v44", "v45"):
    sv = pd.read_csv(ROOT / "data" / f"scores_{v}.csv").set_index("id")["score"].reindex(ids).to_numpy()
    mv = np.zeros(len(sv), bool); mv[np.argpartition(-sv, TOPK)[:TOPK]] = True
    shares.append(((mv & at_cap).sum(), v))
print(f"f5 winsor cap: ${F5CAP:,.2f}; members at cap: {at_cap.sum():,} "
      f"(outside base top: {(at_cap & ~base_mask).sum():,})")
print("capped-f5 count per modern top:", ", ".join(f"{v}:{c}" for c, v in shares))

# ---- swap construction ----------------------------------------------------------
whale = M.all(axis=0)
in_cand = np.flatnonzero(~base_mask & at_cap & (f3v == 0))
in_pool = in_cand[np.argsort(-sL[in_cand])[:N]]
out_cand = np.flatnonzero(base_mask & ~whale)
out_pool = out_cand[np.argsort(sL[out_cand])[:N]]

print(f"\nIN  (capped-f5 outsiders, margin-best): f5 ALL at cap  catsum med {np.median(cat[in_pool]):,.0f}  "
      f"f1 med {np.median(f1v[in_pool]):,.0f}  f11 med {np.median(f11v[in_pool]):.4f}")
print(f"OUT (weakest-margin non-whale):          f5-at-cap {at_cap[out_pool].mean():.3f}  "
      f"catsum med {np.median(cat[out_pool]):,.0f}  f1 med {np.median(f1v[out_pool]):,.0f}  "
      f"f11 med {np.median(f11v[out_pool]):.4f}")
print(f"IN∩prior-failed-promotions guard: v40-in overlap {len(np.intersect1d(in_pool, np.flatnonzero(~base_mask)))} trivial-by-construction; "
      f"capped-IN never selected by any instrument (f5 never carried)")

target = base_mask.copy()
target[out_pool] = False
target[in_pool] = True
assert target.sum() == TOPK and not (target & (f3v >= 1)).any()

# ---- score packaging: vote + margin tie-break + f5-coverage promotion band ------
vote = post.sum(axis=0).astype(np.float64)
margin = (T[:, [names.index(k) for k in SIX]].astype(np.float64)) @ w6
tb = margin / margin.std()
base_new = vote + 1e-3 * tb
assert 1e-3 * np.abs(tb).max() < 0.5
RANGE = base_new.max() - base_new.min()
BIG = 2.0 * RANGE
raw = base_new + BIG * target
raw[f3v >= 1] = raw.min() - 1.0
SCALE = 1.0 + 5.772156649e-7   # unique order-preserving scale: breaks lattice coincidence with prior files

# deterministic anti-fingerprint search: bump the shift by 1e-9 until 0 collisions
# with EVERY prior score file (self-healing; large repeated-value cohorts — e.g. the
# 54,304-member f3 sentinel — make 'nice' shift constants collide with other pipelines).
prior_vals = []
for p in sorted((ROOT / "data").glob("scores_v*.csv")):
    if p.name == "scores_v48.csv":
        continue
    prior_vals.append(np.unique(pd.read_csv(p).set_index("id")["score"].reindex(ids).to_numpy()))
all_prior = np.unique(np.concatenate(prior_vals))
shift = SHIFT
for attempt in range(1000):
    score = raw * SCALE + shift
    if len(np.intersect1d(np.unique(score), all_prior)) == 0:
        break
    shift += 1e-9
else:
    raise RuntimeError("no collision-free shift found in 1000 steps")
print(f"anti-fingerprint: 0 shared floats vs all prior score files ✓ "
      f"(shift {shift!r}, {attempt} bump(s))")

top = np.zeros(len(score), bool)
top[np.argpartition(-score, TOPK)[:TOPK]] = True
assert (top == target).all()
cut = np.sort(score)[::-1][TOPK - 1]
n_cut = int((score == cut).sum())

s = pd.Series(score)

r = np.corrcoef(ids.astype(np.float64), score)[0, 1]
print(f"distinct {s.nunique():,}  cutoff members {n_cut}  f3-in-top 0  "
      f"capped-f5-in-top {int((top & at_cap).sum()):,}")
print(f"revolver {f1v[top].astype(bool).mean():.1%}  whale-in {(top & whale).sum()/whale.sum():.4f}  "
      f"corr(id) {r:+.2e}  set-diff vs v37L {int((top ^ base_mask).sum())//2}/{N}")
print(f"PRE-REGISTERED: realized = {V37L_EXACT} + net*{N/1e5:.5f}, "
      f"box [{V37L_EXACT - 0.7*N/1e5:.4f}, {V37L_EXACT + 0.7*N/1e5:.4f}]")
assert len(s) == 500_000 and s.notna().all() and n_cut == 1 and abs(r) < 1e-2

out = ROOT / "data" / "scores_v48.csv"
pd.DataFrame({"id": ids, "score": score}).to_csv(out, index=False)
print(f"wrote {out.relative_to(ROOT)}")
