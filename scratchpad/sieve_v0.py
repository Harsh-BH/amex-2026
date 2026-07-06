"""F1 generator sieve, pass 1 — enumerate discrete raw-dollar business formulas; keep only
those whose implied readings thread ALL 27 exact public counts (redteam-2026-07-03 §6 F1).

Different in kind from the DE fit: discrete grammar + hard feasibility, not continuous
weights + soft RMSE. The 15-term family's best fit misses readings by up to ±0.010 (χ²≈14);
a form threading 27 windows at ±0.003 is, with overwhelming probability, ~the generator.

Grammar (v0, rates relative to general-spend margin m7 ≡ 1):
  score = f7 + a6·f6 + a8·f8 + a9·f9 + a10·f10          [category margins, per-$ ratios]
        + y·f1                                            [revolve yield ratio]
        − L·f11·(f1 + κ·catsum)                           [expected loss on exposure]
        + r21·f21_k + s19·f19_k + s20·f20_k               [rewards-redeemed, relationship]
        + IMPUT policy for the no-breakdown cohort        [zero vs half-cohort-median]
  f3=1 → hard evict (triple-validated). Missing → 0 except per policy.
Acceptance: max_j |implied_j − OBS_j| over all 27 readings; report the top-200 threaders.

Run: .venv/bin/python scratchpad/sieve_v0.py   (multiprocess; ~30-60 min pass 1)
"""
from pathlib import Path
import itertools
import numpy as np
import pandas as pd
from multiprocessing import Pool

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
M = z["M"]
keys = [str(x) for x in z["obs_keys"]]
assert "v36" in keys and "v37L" in keys, "cache stale"
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from triangulate2 import OBS
obs = np.array([OBS[k] for k in keys])

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
ids = df["id"].to_numpy()
assert (ids == z["ids"]).all()
f = df.fillna(0.0)
F6, F7, F8, F9, F10 = (f[c].to_numpy(np.float64) for c in ("f6", "f7", "f8", "f9", "f10"))
F1, F11 = f["f1"].to_numpy(np.float64), f["f11"].to_numpy(np.float64)
F21, F19, F20, F3 = f["f21"].to_numpy(np.float64), f["f19"].to_numpy(np.float64), f["f20"].to_numpy(np.float64), f["f3"].to_numpy(np.float64)
CAT = F6 + F7 + F8 + F9 + F10
nbd = df["f6"].isna().to_numpy()

# scale count-like / heavy features to raw-dollar-comparable units so grid ratios are sane
F21k = F21 / 1_000.0        # points redeemed in thousands
F19k = F19 * 1_000.0        # per supp account, $1K-margin units
F20k = F20 * 1_000.0
med_cat = np.median(CAT[~nbd & (CAT > 0)])
IMPUT_HALF = np.where(nbd, 0.5 * med_cat, 0.0)   # policy B: credit nbd half the median catsum

evict = F3 == 1

# grid (64,800 combos): seeded from the decoded economics (yield ~15x interchange, lodging +,
# airline/dining ~0, breakeven f11 ~0.10-0.20 → L ≈ y/f11*)
GRID = list(itertools.product(
    (-2.0, 0.0, 2.0),           # a6  airline
    (0.0, 1.0, 2.0),            # a8  entertainment
    (0.0, 2.0, 4.0, 6.0, 8.0),  # a9  lodging
    (0.0, 0.5, 1.0),            # a10 dining
    (8.0, 10.0, 12.0, 14.0, 16.0, 20.0),   # y   revolve yield ratio
    (60.0, 80.0, 100.0, 120.0, 150.0),     # L   loss multiplier
    (0.0, 0.3),                 # κ   loss also on spend receivables
    (0.0, 1.0),                 # r21 rewards-redeemed ($/k-pt units)
    (0.0, 0.3),                 # s19 supp accounts
    (0.0, 1.0),                 # imput policy weight (0 = zero-fill, 1 = half-median credit)
))
print(f"grid size: {len(GRID):,}")


def eval_batch(batch):
    out = []
    for (a6, a8, a9, a10, y, L, kap, r21, s19, imw) in batch:
        s = (F7 + a6 * F6 + a8 * F8 + a9 * F9 + a10 * F10
             + y * F1 - L * F11 * (F1 + kap * CAT)
             + r21 * F21k + s19 * F19k + imw * IMPUT_HALF)
        s[evict] = -1e18
        idx = np.argpartition(-s, TOPK)[:TOPK]
        ov = M[:, idx].sum(axis=1) / TOPK
        err = np.abs(ov - obs)
        out.append((float(err.max()), float(np.sqrt((err ** 2).mean())),
                    a6, a8, a9, a10, y, L, kap, r21, s19, imw))
    return out


if __name__ == "__main__":
    B = 250
    batches = [GRID[i:i + B] for i in range(0, len(GRID), B)]
    rows = []
    with Pool(6) as pool:
        for j, res in enumerate(pool.imap_unordered(eval_batch, batches)):
            rows.extend(res)
            if (j + 1) % 20 == 0:
                best = min(r[0] for r in rows)
                print(f"batch {j+1}/{len(batches)}  evaluated {len(rows):,}  best max|err| {best:.4f}", flush=True)
    rows.sort(key=lambda r: r[0])
    cols = ["max_err", "rmse", "a6", "a8", "a9", "a10", "y", "L", "kappa", "r21", "s19", "imput"]
    top = pd.DataFrame(rows[:200], columns=cols)
    top.to_csv(ROOT / "scratchpad" / "sieve_v0_top200.csv", index=False)
    n_thread = sum(1 for r in rows if r[0] <= 0.003)
    n_near = sum(1 for r in rows if r[0] <= 0.005)
    print(f"\nDONE {len(rows):,} forms | threaders (max|err| ≤ 0.003): {n_thread} | near (≤ 0.005): {n_near}")
    print(top.head(15).to_string(index=False))
    print("reference: the 15-term DE family's best fit has per-reading errors up to ±0.010")
