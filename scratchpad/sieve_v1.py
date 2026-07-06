"""F1 generator sieve, pass 2 — regime-aware raw-dollar grammar (redteam §6 F2 folded into F1).

Pass 1 (sieve_v0): flat raw-dollar grammar FALSIFIED — best max|err| 0.0116, diffuse across
eras. Pass 2 adds what no submission ever probed: per-availability-regime offsets
(rewards-inactive = f4&f21 co-missing, 51.4% of pop; no-lend-line = f17 missing, ~59%;
no-breakdown = f6 missing, 23%), crossed with a fine grid around pass 1's best economics
(a9≈6, a8≈2, y≈16, L≈120). Acceptance unchanged: thread all 27 exact readings.

Run: .venv/bin/python scratchpad/sieve_v1.py   (multiprocess; ~40-70 min)
"""
from pathlib import Path
import itertools
import numpy as np
import pandas as pd
from multiprocessing import Pool
import sys

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
sys.path.insert(0, str(Path(__file__).resolve().parent))
from triangulate2 import OBS

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
M = z["M"]
keys = [str(x) for x in z["obs_keys"]]
assert "v37L" in keys
obs = np.array([OBS[k] for k in keys])

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == z["ids"]).all()
f = df.fillna(0.0)
F6, F7, F8, F9, F10 = (f[c].to_numpy(np.float64) for c in ("f6", "f7", "f8", "f9", "f10"))
F1, F11, F3 = f["f1"].to_numpy(np.float64), f["f11"].to_numpy(np.float64), f["f3"].to_numpy(np.float64)
CAT = F6 + F7 + F8 + F9 + F10
nbd = df["f6"].isna().to_numpy()
rew_inact = df["f4"].isna().to_numpy()          # rewards-inactive (f4/f21 co-missing, A3)
no_line = df["f17"].isna().to_numpy()           # charge-only / no lend line (A4)
med_cat = np.median(CAT[~nbd & (CAT > 0)])
IMPUT_HALF = np.where(nbd, 0.5 * med_cat, 0.0)
evict = F3 == 1
REW = rew_inact.astype(np.float64)
NLN = no_line.astype(np.float64)

# fine base grid around pass-1 optimum × regime offsets (units: raw dollars of score)
BASE = list(itertools.product(
    (-1.0, 0.0, 1.0),               # a6 airline
    (1.5, 2.0, 2.5),                # a8 entertainment
    (5.0, 6.0, 7.0),                # a9 lodging
    (0.0, 0.25),                    # a10 dining
    (14.0, 15.0, 16.0, 17.0, 18.0), # y yield
    (100.0, 110.0, 120.0, 130.0),   # L loss
    (0.0, 0.5, 1.0),                # imput weight
))
OFFS = list(itertools.product(
    (-15000.0, -5000.0, 0.0, 5000.0, 15000.0),   # rewards-inactive offset
    (-15000.0, -5000.0, 0.0, 5000.0, 15000.0),   # no-lend-line offset
))
GRID = [b + o for b in BASE for o in OFFS]
print(f"grid size: {len(GRID):,}")


def eval_batch(batch):
    out = []
    for (a6, a8, a9, a10, y, L, imw, o_rew, o_nln) in batch:
        s = (F7 + a6 * F6 + a8 * F8 + a9 * F9 + a10 * F10
             + y * F1 - L * F11 * F1 + imw * IMPUT_HALF
             + o_rew * REW + o_nln * NLN)
        s[evict] = -1e18
        idx = np.argpartition(-s, TOPK)[:TOPK]
        ov = M[:, idx].sum(axis=1) / TOPK
        err = np.abs(ov - obs)
        out.append((float(err.max()), float(np.sqrt((err ** 2).mean())),
                    a6, a8, a9, a10, y, L, imw, o_rew, o_nln))
    return out


if __name__ == "__main__":
    B = 250
    batches = [GRID[i:i + B] for i in range(0, len(GRID), B)]
    rows = []
    with Pool(6) as pool:
        for j, res in enumerate(pool.imap_unordered(eval_batch, batches)):
            rows.extend(res)
            if (j + 1) % 40 == 0:
                best = min(r[0] for r in rows)
                print(f"batch {j+1}/{len(batches)}  evaluated {len(rows):,}  best max|err| {best:.4f}", flush=True)
    rows.sort(key=lambda r: r[0])
    cols = ["max_err", "rmse", "a6", "a8", "a9", "a10", "y", "L", "imput", "off_rew", "off_nln"]
    pd.DataFrame(rows[:200], columns=cols).to_csv(ROOT / "scratchpad" / "sieve_v1_top200.csv", index=False)
    n_thread = sum(1 for r in rows if r[0] <= 0.003)
    n_near = sum(1 for r in rows if r[0] <= 0.005)
    print(f"\nDONE {len(rows):,} | threaders ≤0.003: {n_thread} | near ≤0.005: {n_near}")
    print(pd.DataFrame(rows[:12], columns=cols).to_string(index=False))
    print("pass-1 reference: flat grammar best max|err| 0.0116; 15-term family RMSE 0.0037")
