"""Build data/scores_v36.csv — v36 'dual form probe' (bounded OUT-OF-FAMILY trust-region probe).

Context (experiment-history 2026-07-03): the in-family conviction pool is measured near-dry
(v35 net accuracy +0.074 vs v34's +0.436); remaining in-family yield ~ +0.002 total; the pack
(0.929-0.930) holds ~ +0.010 of out-of-family structure. This probe spends bounded swaps on the
two most defensible NEVER-BASIS-TESTED axes, disjoint by construction, on top of v35's banked set:

  A. UTILIZATION BASIS (cap 1,500): for lend-line members (f17>0, f1>0, non-nbd), re-express the
     lending signal as the within-line-cohort quantile of f1 (deciles of f17). Hypothesis: the
     truth prices balance relative to granted line; dollar basis mis-ranks the boundary there.
  B. NBD REORDER AT HELD LEVEL (cap 600): within the no-breakdown cohort, re-order by margin +
     0.39·z(imputed spend) (A15 imputer, OOS Spearman 0.46 — a real measured signal); the COUNT
     of nbd members in the top quintile is held exactly (v9 proved level-shifts lose; ordering
     at held level was never LB-tested).

Both components keep the P&L weight ratios fixed (0.70/0.39/0.19/0.002/-0.57), swap only where
the modified basis most strongly disagrees with v35's set, hard f3 screen, whale guard.
Box: realized = 0.919 + (r_in - r_out)·N/1e5, N ≤ 2,100 → [0.898, 0.940]. Banked 0.919 safe.

Run: .venv/bin/python scratchpad/build_v36_probe.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
CAP_UTIL, CAP_NBD = 1_500, 600
W = {"f1": 0.70, "f7": 0.39, "f9": 0.19, "f10": 0.002, "exl": 0.57}  # v35 central calibration

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
ids = df["id"].to_numpy()
f = df.fillna(0.0)
f1, f7, f9, f10, f11, f17, f3 = (f[c].to_numpy() for c in ("f1", "f7", "f9", "f10", "f11", "f17", "f3"))
nbd = df["f6"].isna().to_numpy()
cat = f[["f6", "f7", "f8", "f9", "f10"]].sum(axis=1).to_numpy()

def z(v):
    return v / (v.std() + 1e-9)

margin = W["f1"]*z(f1) + W["f7"]*z(f7) + W["f9"]*z(f9) + W["f10"]*z(f10) - W["exl"]*z(f11*f1)

s35 = pd.read_csv(ROOT / "data" / "scores_v35.csv").set_index("id")["score"].reindex(ids).to_numpy()
m35 = np.zeros(len(s35), bool)
m35[np.argpartition(-s35, TOPK)[:TOPK]] = True
assert not (m35 & (f3 == 1)).any()

# ---- component A: utilization-basis lending signal ----
# u$ = within-f17-decile rank of f1, quantile-MATCHED back to the global f1 dollar distribution:
# same marginal distribution as f1 (no tail-crushing — the demote-high-f1 direction is LB-dead),
# only members whose within-cohort rank mismatches their global rank move.
lend_pop = (f17 > 0) & (f1 > 0) & ~nbd
dec = pd.qcut(pd.Series(f17[lend_pop]), 10, labels=False, duplicates="drop").to_numpy()
f1_lp = f1[lend_pop]
rank_in_cohort = np.zeros(lend_pop.sum())
for d in np.unique(dec):
    m = dec == d
    rank_in_cohort[m] = pd.Series(f1_lp[m]).rank(pct=True).to_numpy()
u_dollar = np.quantile(f1_lp, np.clip(rank_in_cohort, 0, 1))
u = f1.copy()
u[lend_pop] = u_dollar
delta_a = W["f1"] * (z(u) - z(f1))                    # pure form-axis disagreement (dollar-preserving)
margin_util = margin + delta_a
util_scope = lend_pop & (f3 == 0)

d_in = np.where(~m35 & util_scope, delta_a, -np.inf)   # outsiders the form PROMOTES hardest
d_out = np.where(m35 & util_scope, -delta_a, -np.inf)  # insiders the form DEMOTES hardest
in_a = np.argsort(-d_in)[:CAP_UTIL]
out_a = np.argsort(-d_out)[:CAP_UTIL]
in_a = in_a[d_in[in_a] > 0]                            # require a genuinely positive form push
out_a = out_a[d_out[out_a] > 0]
n_a = min(len(in_a), len(out_a), CAP_UTIL)
in_a, out_a = in_a[:n_a], out_a[:n_a]

# ---- component B: nbd reorder at held level ----
bd = ~nbd
X_cols = ["f4", "f21", "f1", "f11", "f12", "f13", "f14", "f15", "f16"]
X = np.column_stack([np.log1p(f[c].to_numpy().clip(min=0)) for c in X_cols])
Xb = np.column_stack([X, np.ones(len(X))])
beta, *_ = np.linalg.lstsq(Xb[bd], np.log1p(cat[bd].clip(min=0)), rcond=None)
imput = Xb @ beta
nbd_order = margin + W["f7"] * z(np.where(nbd, imput, 0.0))
nbd_scope = nbd & (f3 == 0)
b_in = np.where(~m35 & nbd_scope, nbd_order, -np.inf)
b_out = np.where(m35 & nbd_scope, -nbd_order, -np.inf)
in_b = np.argsort(-b_in)[:CAP_NBD]
out_b = np.argsort(-b_out)[:CAP_NBD]
in_b = in_b[b_in[in_b] > -np.inf]
out_b = out_b[b_out[out_b] > -np.inf]
n_b = min(len(in_b), len(out_b), CAP_NBD)
in_b, out_b = in_b[:n_b], out_b[:n_b]     # held level: equal in/out within the cohort

assert not (set(in_a) & set(in_b)) and not (set(out_a) & set(out_b))
swap_in = np.concatenate([in_a, in_b])
swap_out = np.concatenate([out_a, out_b])
N = len(swap_in)
print(f"component A (utilization): {n_a} pairs   component B (nbd held-level): {n_b} pairs   total N = {N}")
for nm, mm in (("IN-A", in_a), ("OUT-A", out_a), ("IN-B", in_b), ("OUT-B", out_b)):
    print(f"  {nm:>6}: f1 med {np.median(f1[mm]):>9,.0f}  f17 med {np.median(f17[mm]):>9,.0f}"
          f"  catsum med {np.median(cat[mm]):>9,.0f}  f11 med {np.median(f11[mm]):.4f}")

target = m35.copy()
target[swap_out] = False
target[swap_in] = True
assert target.sum() == TOPK and not (target & (f3 == 1)).any()

# natural own-scale score: form-consensus base (margin averaged over the two modified bases)
base = 0.5 * (margin_util + nbd_order)
BIG = 2.0 * (base.max() - base.min())
score = base + BIG * target
score[f3 == 1] = score.min() - 1.0
score = score + 0.3141592653          # global shift distinct from v34/v35

s = pd.Series(score)
top = np.zeros(len(s), bool)
top[np.argpartition(-score, TOPK)[:TOPK]] = True
assert (top == target).all()
cut = np.sort(score)[::-1][TOPK - 1]
n_cut = int((score == cut).sum())
for prior in ("scores_v35", "scores_v34", "scores_v29"):
    pv = pd.read_csv(ROOT / "data" / f"{prior}.csv").set_index("id")["score"].reindex(ids).to_numpy()
    shared = np.intersect1d(np.unique(score), np.unique(pv))
    print(f"floats shared with {prior}: {len(shared)} (must be 0)")
    assert len(shared) == 0

print(f"distinct: {s.nunique():,}   cutoff members: {n_cut}   f3 in top: {int((top & (f3==1)).sum())}")
print(f"revolver share: {f1[top].astype(bool).mean():.1%}   overlap vs v35: {(top & m35).sum()/TOPK:.4f}")
r = np.corrcoef(ids.astype(np.float64), score)[0, 1]
print(f"corr(id, score): {r:+.2e}")
print(f"BOX: realized = 0.919 + (r_in − r_out)·{N/1e5:.5f} ∈ [{0.919 - N/1e5:.4f}, {0.919 + N/1e5:.4f}]")
assert len(s) == 500_000 and s.notna().all() and n_cut == 1 and abs(r) < 1e-2

pd.DataFrame({"id": ids, "score": score}).to_csv(ROOT / "data" / "scores_v36.csv", index=False)
print("wrote data/scores_v36.csv")
