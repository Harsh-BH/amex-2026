"""Constraint projection — the set-level architecture.

The 21 observed overlaps are EXACT count equations on the truth's top-100K:
    sum_{i in top_k} x_i = obs_k * 100,000  (+/- ~150 public-sampling noise)   for each submission k
    sum_i x_i = 100,000
where x_i = P(member i is in the truth's top quintile). The formula-fit only satisfies these
through a 15-weight bottleneck; the posterior vote prior p_i = vote_i/K satisfies them only
approximately. This script measures the violation (the information the formulas discard) and
projects p onto the constraint polytope:  min ||x - p||^2  s.t.  A x = b, 0 <= x <= 1
via the box-constrained dual (x = clip(p + A^T lam, 0, 1), Newton on the 22-dim dual).

Run: .venv/bin/python scratchpad/tri2_project.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
M, ids = z["M"], z["ids"]                     # 21 x 500K observed masks
keys = [str(x) for x in z["obs_keys"]]
from triangulate2 import OBS                   # noqa: E402  (same dir import)
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
post = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")   # 29 x 500K
K = post.shape[0]
p = post.sum(0).astype(np.float64) / K         # prior membership probability

A = np.vstack([M.astype(np.float64), np.ones((1, M.shape[1]))])    # 22 x 500K
b = np.array([OBS[k] * TOPK for k in keys] + [float(TOPK)])

print("=== prior violation of the exact count constraints (the discarded information) ===")
viol = A @ p - b
for k, v in zip(keys + ["total"], viol):
    print(f"  {k:>6}: prior {A[keys.index(k) if k != 'total' else -1] @ p:10.0f}  target {b[keys.index(k) if k != 'total' else -1]:10.0f}  gap {v:+8.0f}")
print(f"  max |gap| {np.abs(viol).max():.0f} members   rms {np.sqrt((viol**2).mean()):.0f}")

# dual Newton for the box-constrained projection
lam = np.zeros(22)
for it in range(200):
    raw = p + A.T @ lam
    x = np.clip(raw, 0.0, 1.0)
    g = A @ x - b
    if np.abs(g).max() < 1.0:                  # within 1 member on every constraint
        break
    active = ((raw > 0) & (raw < 1)).astype(np.float64)
    J = (A * active) @ A.T + 1e-6 * np.eye(22)
    lam -= np.linalg.solve(J, g)
print(f"projection converged in {it+1} iters; residual max |gap| {np.abs(A @ x - b).max():.1f} members")

# how different is the projected ranking from the prior ranking?
top_prior = np.zeros(len(p), bool); top_prior[np.argpartition(-p, TOPK)[:TOPK]] = True
top_proj = np.zeros(len(p), bool);  top_proj[np.argpartition(-x, TOPK)[:TOPK]] = True
moved = int((top_prior != top_proj).sum() // 2)
print(f"\nPROJECTION STEP: {moved:,} members cross the top-100K boundary (prior vote vs projected)")
print(f"projected top vs v29: {(top_proj & M[keys.index('v29')]).sum()/TOPK:.4f}  "
      f"vs v30: {(top_proj & M[keys.index('v30')]).sum()/TOPK:.4f}")
df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
f3 = df["f3"].fillna(0).to_numpy()
print(f"f3=1 members in projected top: {int((top_proj & (f3 == 1)).sum()):,}")
ov = [(top_proj & q).sum() / TOPK for q in post]
print(f"projected candidate under posterior: E[LB] {np.mean(ov):.4f}  min {np.min(ov):.4f}  max {np.max(ov):.4f}")
pd.DataFrame({"id": ids, "score": x + 1e-9 * p}).to_csv(ROOT / "scratchpad" / "tri2_projected_scores.csv", index=False)
print("saved scratchpad/tri2_projected_scores.csv")
