"""Falsification battery for the HOLD conclusion — three attacks, all zero submission cost.

A. RESIDUAL FORENSICS: which constraints does the family systematically strain (per-constraint
   signed residual across the kept posterior)? A shared member-type behind the strain = a
   nameable missing term the six-term screens could have missed.
B. LP BOUNDS: at the pure-arithmetic level (count constraints as intervals, obs +/- 0.002),
   how many f3=1 members CAN the truth's top-100K contain? (Every post-v10 submission
   hard-evicts them, so the posterior prior ~0 may be assumption, not inference.)
C. CVaR CANDIDATE: the percentile-edge model (realized LB has landed at the ~6th/25th/15th
   percentile of each candidate's predicted-overlap distribution — mean-model errors
   +0.037/+0.009/+0.017 vs percentile-model ~0.001-0.005) implies the SHIP objective should be
   a candidate's LOW QUANTILE across the posterior, not its mean. The consensus vote maximizes
   the mean; here we solve the maximin/CVaR set-selection LP and compare distributions.

Run: cd scratchpad && ../.venv/bin/python tri2_falsify.py
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triangulate2 as t2
from scipy.optimize import linprog

TOPK = 100_000
T, M, ids, names, keys = t2.load()                      # M: 21 x 500K observed masks
post = np.load(t2.ROOT / "scratchpad" / "tri2_posterior_masks.npy")   # 29 x 500K
K = post.shape[0]
df = pd.read_pickle(t2.ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
f3 = (df["f3"].fillna(0).to_numpy() == 1)

# ---------- A. per-constraint residual forensics ----------
print("=== A. per-constraint signed residuals (mean across kept posterior) ===")
res = {k: [] for k in keys}
for j in range(K):
    tidx = np.flatnonzero(post[j])
    for i, k in enumerate(keys):
        res[k].append(M[i, tidx].sum() / TOPK - t2.OBS[k])
for k in keys:
    r = np.array(res[k])
    flag = " <-- STRAIN" if abs(r.mean()) > 0.003 else ""
    print(f"  {k:>6}: mean {r.mean():+.4f}  sd {r.std():.4f}{flag}")

# ---------- B. LP bound on f3 membership in the truth ----------
print("\n=== B. LP: how many f3 members can the truth's top-100K contain? ===")
pat = np.zeros(M.shape[1], dtype=np.uint32)
for i in range(M.shape[0]):
    pat |= (M[i].astype(np.uint32) << i)
pat = pat.astype(np.int64) * 2 + f3.astype(np.int64)     # refine cells by the f3 flag
vals, inv, counts = np.unique(pat, return_inverse=True, return_counts=True)
C = len(vals)
Acell = np.zeros((21, C))
for i in range(21):
    inc = (vals // 2) & (1 << i) > 0
    Acell[i] = inc.astype(float)
f3cell = (vals % 2 == 1).astype(float)
b = np.array([t2.OBS[k] * TOPK for k in keys])
slack = 200.0                                            # obs read noise ~ +/-0.002 * 100K
A_ub = np.vstack([Acell, -Acell, np.ones((1, C)), -np.ones((1, C))])
b_ub = np.concatenate([b + slack, -(b - slack), [TOPK + 1], [-(TOPK - 1)]])
for sense, cvec in (("MAX", -f3cell * 1.0), ("MIN", f3cell * 1.0)):
    r = linprog(cvec * counts, A_ub=A_ub * counts[None, :], b_ub=b_ub,
                bounds=[(0, 1)] * C, method="highs")
    val = abs(r.fun)
    print(f"  {sense} f3 members in truth-top (pure arithmetic): {val:,.0f}   (status {r.status})")

# ---------- C. CVaR / maximin candidate vs the consensus ----------
print("\n=== C. robust (low-quantile) candidate vs mean-optimal consensus ===")
pat2 = np.zeros(M.shape[1], dtype=np.uint64)
for j in range(min(K, 60)):
    pat2 |= (post[j].astype(np.uint64) << np.uint64(j))
vals2, inv2, cnt2 = np.unique(pat2, return_inverse=True, return_counts=True)
C2 = len(vals2)
print(f"posterior-mask cells: {C2:,}")
Pcell = np.zeros((K, C2))
for j in range(K):
    Pcell[j] = ((vals2 >> np.uint64(j)) & np.uint64(1)).astype(float)
# LP: max t  s.t.  for all j: sum_c y_c * P_jc >= t ;  sum y = TOPK ; 0<=y_c<=n_c
# vars = [y_1..y_C2, t]
cvec = np.zeros(C2 + 1); cvec[-1] = -1.0
A_ub2 = np.hstack([-Pcell, np.ones((K, 1))])             # t - P y <= 0
b_ub2 = np.zeros(K)
A_eq = np.hstack([np.ones((1, C2)), np.zeros((1, 1))])
r2 = linprog(cvec, A_ub=A_ub2, b_ub=b_ub2, A_eq=A_eq, b_eq=[TOPK],
             bounds=[(0, c) for c in cnt2] + [(0, TOPK)], method="highs")
y = r2.x[:C2]
print(f"maximin LP: worst-case overlap = {r2.x[-1]/TOPK:.4f} (consensus worst-case was 0.887)")
# realize the fractional cells into a concrete ranking: members ordered by y_c/n_c then margin
frac = y / np.maximum(cnt2, 1)
member_pri = frac[inv2]
w6 = np.load(t2.ROOT / "scratchpad" / "tri2_fit6_w.npy")
SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]
margin = T[:, [names.index(k) for k in SIX]].astype(np.float64) @ w6
score = member_pri + 1e-6 * (margin / margin.std())
top = np.zeros(len(score), bool); top[np.argpartition(-score, TOPK)[:TOPK]] = True
ov = np.array([(top & post[j]).sum() / TOPK for j in range(K)])
q = np.percentile(ov, [5, 15, 50, 85])
print(f"CVaR candidate distribution: min {ov.min():.4f}  q15 {q[1]:.4f}  med {q[2]:.4f}  mean {ov.mean():.4f}")
print(f"  edge-model prediction (q10-q25 band): {np.percentile(ov,10):.4f} - {np.percentile(ov,25):.4f}")
s31 = pd.read_csv(t2.ROOT / "data" / "scores_v31.csv").set_index("id")["score"].reindex(ids).to_numpy()
t31 = np.zeros(len(s31), bool); t31[np.argpartition(-s31, TOPK)[:TOPK]] = True
ov31 = np.array([(t31 & post[j]).sum() / TOPK for j in range(K)])
print(f"v31 (mean-optimal) distribution:  min {ov31.min():.4f}  q15 {np.percentile(ov31,15):.4f}  "
      f"med {np.percentile(ov31,50):.4f}  mean {ov31.mean():.4f}")
print(f"CVaR vs v31 overlap: {(top & t31).sum()/TOPK:.4f}   CVaR vs v29: "
      f"{(top & M[keys.index('v29')]).sum()/TOPK:.4f}   f3 in CVaR top: {int((top & f3).sum())}")
pd.DataFrame({"id": ids, "score": score}).to_csv(t2.ROOT / "scratchpad" / "tri2_cvar_scores.csv", index=False)
print("saved scratchpad/tri2_cvar_scores.csv")
