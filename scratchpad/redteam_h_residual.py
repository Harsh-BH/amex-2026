"""Red-team diagnostic: does a NEVER-MODELED term explain the family's reading residuals?

Logic: if the hidden truth contains a term h OUTSIDE the 15-term family, then historical
candidates whose top-100K happened to carry more high-h members should systematically
OUTPERFORM their family-implied reading (and vice versa for a truth-negative h).
Detector: Spearman(actual - implied, rank-mean of h within the candidate's top set)
across all 27 exact LB readings.
Negative controls: in-family terms (f1, f7 — their effect is already inside `implied`,
so rho should be ~0) and a random permutation (noise floor).

Light (no optimizer) — safe to run alongside the live refit.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr

ROOT = Path("/home/harsh1/github-repos/amex-2026")
K = 100_000

OBS = {"v1": .449, "v2": .465, "v3": .614, "v4": .609, "v5": .733, "v6": .675, "v7": .768,
       "v8": .681, "v9": .727, "v10": .805, "v11min": .823, "v15": .827, "v19": .859,
       "v21": .851, "v22": .866, "v24": .880, "v25": .866, "v26": .843, "v27": .895,
       "v29": .915, "v30": .904, "v32": .912, "v33": .907, "v34": .917614,
       "v35": .918971, "v37L": .919143, "v36": .917386}

# 6-term restricted-fit implied readings, copied from refit27_log.txt (RMSE 0.0064 run)
FIT6 = {"v1": .462, "v2": .476, "v3": .623, "v4": .617, "v5": .733, "v6": .681, "v7": .767,
        "v8": .688, "v9": .727, "v10": .810, "v11min": .829, "v15": .824, "v19": .854,
        "v21": .844, "v22": .864, "v24": .874, "v25": .857, "v26": .834, "v27": .898,
        "v29": .917, "v30": .894, "v32": .913, "v33": .909, "v34": .921, "v35": .925,
        "v37L": .924, "v36": .921}

print("=== 0. metric denominator check: 6-dp readings x 70,000 should be integers ===")
for label, v in [("v34", .917614), ("v35", .918971), ("v37L", .919143), ("v36", .917386),
                 ("LB#1", .932814), ("LB#2", .930129), ("LB#3", .9296), ("LB#4", .929286)]:
    n = v * 70_000
    print(f"  {label:>5} {v:.6f} -> {n:.2f}  (dist to integer {abs(n - round(n)):.3f})")

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
T, M = z["T"], z["M"]
names = [str(x) for x in z["names"]]
keys = [str(x) for x in z["obs_keys"]]
CORE = names[:15]
assert M.shape[0] == len(keys) == 27, f"cache has {M.shape[0]} masks / {len(keys)} keys"

w = np.load(ROOT / "scratchpad" / "tri2_core_w.npy")
score15 = T[:, :15] @ w.astype(np.float32)
top15 = np.zeros(T.shape[0], bool)
top15[np.argpartition(-score15, K)[:K]] = True
implied15 = {k: (M[i] & top15).sum() / K for i, k in enumerate(keys)}

res15 = np.array([OBS[k] - implied15[k] for k in keys])
res6 = np.array([OBS[k] - FIT6[k] for k in keys])
print("\n=== 1. residuals (actual - implied), 15-term single best fit (fresh core_w) ===")
for i, k in enumerate(keys):
    print(f"  {k:>6}: actual {OBS[k]:.4f} implied15 {implied15[k]:.4f} res15 {res15[i]:+.4f}  res6 {res6[i]:+.4f}")
print(f"  RMSE15 {np.sqrt((res15**2).mean()):.4f}   RMSE6 {np.sqrt((res6**2).mean()):.4f}")

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert len(df) == T.shape[0]

cands: dict[str, np.ndarray] = {}
for c in ["f19", "f20", "f23", "f22", "f12", "f5", "f13", "f14", "f15", "f16",
          "f2", "f4", "f21", "f17", "f18"]:
    cands[c] = df[c].fillna(0).to_numpy(float)
cands["miss_rewards(f4na)"] = df["f4"].isna().to_numpy(float)
cands["miss_line(f17na)"] = df["f17"].isna().to_numpy(float)
cands["miss_nbd(f6na)"] = df["f6"].isna().to_numpy(float)
cands["CTRL_f1_infam"] = df["f1"].fillna(0).to_numpy(float)
cands["CTRL_f7_infam"] = df["f7"].fillna(0).to_numpy(float)
rng = np.random.default_rng(0)
cands["CTRL_random"] = rng.permutation(len(df)).astype(float)

print("\n=== 2. residual-vs-capture regression over the 27 exact readings ===")
print("(capture_i = mean percentile-rank of h within candidate i's top-100K;")
print(" rho>0 -> truth REWARDS h beyond the family; rho<0 -> truth PENALIZES h; controls ~0)")
print(f"{'term':22} {'miss%':>6} {'rho15':>7} {'p15':>7} {'rho6':>7} {'p6':>7}   capture range")
results = []
caps_store = {}
for name in cands:
    v = cands[name]
    r = pd.Series(v).rank(pct=True).to_numpy(np.float32)
    cap = np.array([r[M[i]].mean() for i in range(len(keys))])
    caps_store[name] = cap
    rho15, p15 = spearmanr(res15, cap)
    rho6, p6 = spearmanr(res6, cap)
    misspct = 100.0 * float(df[name].isna().mean()) if name in df.columns else 0.0
    results.append((name, misspct, rho15, p15, rho6, p6, cap.min(), cap.max()))
for name, misspct, rho15, p15, rho6, p6, cmin, cmax in sorted(results, key=lambda t: -abs(t[2])):
    flag = " <<<" if (abs(rho15) > 0.5 and abs(rho6) > 0.4 and np.sign(rho15) == np.sign(rho6)
                     and not name.startswith("CTRL")) else ""
    print(f"{name:22} {misspct:6.1f} {rho15:+7.3f} {p15:7.4f} {rho6:+7.3f} {p6:7.4f}   [{cmin:.3f},{cmax:.3f}]{flag}")

print("\n=== 3. capture cross-correlation of flagged terms vs controls (discrimination check) ===")
flagged = [t[0] for t in results if abs(t[2]) > 0.5 and not t[0].startswith("CTRL")]
for name in flagged:
    c1 = np.corrcoef(caps_store[name], caps_store["CTRL_f1_infam"])[0, 1]
    c7 = np.corrcoef(caps_store[name], caps_store["CTRL_f7_infam"])[0, 1]
    print(f"  {name:22} corr(cap, cap_f1) {c1:+.3f}  corr(cap, cap_f7) {c7:+.3f}")

print("\n=== 4. current-set composition (v35 top-100K) and the two never-probed cohorts ===")
s35 = pd.read_csv(ROOT / "data" / "scores_v35.csv").set_index("id")["score"].reindex(df["id"]).to_numpy()
S = np.zeros(len(df), bool)
S[np.argpartition(-s35, K)[:K]] = True
votes = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
vote = votes.sum(0)
Kc = votes.shape[0]
core_in = S & (vote == Kc)
contested_in = S & (vote < Kc)
contested_out = (~S) & (vote > 0)
never = ~M.any(axis=0)
print(f"  posterior calibrations Kc={Kc}; S-core(all votes) {core_in.sum():,}; "
      f"S-contested {contested_in.sum():,}; out-contested {contested_out.sum():,}; "
      f"never-in-any-of-27-tops {never.sum():,}")
print(f"{'term':22} {'pop':>6} {'S':>6} {'S-cont':>7} {'out-cont':>8} {'never':>6}")
for name in ["f19", "f20", "f23", "f22", "f5", "f13", "f14", "f15", "f16",
             "miss_rewards(f4na)", "miss_line(f17na)"]:
    r = pd.Series(cands[name]).rank(pct=True).to_numpy(np.float32)
    print(f"{name:22} {r.mean():6.3f} {r[S].mean():6.3f} {r[contested_in].mean():7.3f} "
          f"{r[contested_out].mean():8.3f} {r[never].mean():6.3f}")
print("\ncohort shares:")
for name in ["miss_rewards(f4na)", "miss_line(f17na)", "miss_nbd(f6na)"]:
    v = cands[name]
    print(f"  {name:22} pop {v.mean():.3f}  in-S {v[S].mean():.3f}")
