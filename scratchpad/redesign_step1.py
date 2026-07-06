"""Redesign implementation, step 1 (report §15.1):
  A. Gibbs-eta reweighting of the fresh 30-constraint ensemble, with (eta, tau) calibrated
     so the 8 paid designed-probe outcomes achieve uniform PIT coverage (SafeBayes-style).
  B. Eigen-probe designer: top eigenvectors of the reweighted boundary co-membership
     covariance -> concrete swap-pool specs with EIG estimates (the next bench reads).
  C. v44 candidate: v42-pattern tranche (reweighted votes, pu-veto) off v37L base, gated
     by the CALIBRATED predictive instead of the raw vote-gap heuristic.
"""
from pathlib import Path
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
K = 100_000
SIGMA = 0.001                     # measured read noise (A42)

OBS = {"v29": .915, "v33": .907, "v34": .917614, "v35": .918971, "v36": .917386,
       "v37L": .919143, "v40": .914, "v41": .917643, "v43": .912}
# probes: (probe, base) with realized reads; pools derived from set-diffs
PROBES = [("v33", "v29"), ("v34", "v29"), ("v35", "v34"), ("v36", "v35"),
          ("v37L", "v35"), ("v41", "v35"), ("v40", "v35"), ("v43", "v37L")]

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
M_hist, ids = z["M"], z["ids"]
names = [str(x) for x in z["names"]]
masks = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
Kc = masks.shape[0]

log = (ROOT / "scratchpad" / "refit30_log.txt").read_text()
sect = log.split("=== E. posterior")[0:]
seed_rmse = [(int(a), float(b)) for a, b in re.findall(r"seed (\d+): RMSE ([0-9.]+)", log)]
seed_rmse = seed_rmse[-48:]                          # posterior section = last 48 entries
rs = np.array([r for _, r in seed_rmse])
keep_mask = rs <= rs.min() * 1.5 + 1e-6
kept_rmse = rs[keep_mask]
assert keep_mask.sum() == Kc, f"log kept {keep_mask.sum()} vs masks {Kc}"
print(f"A. ensemble: {Kc} kept calibrations, RMSE {kept_rmse.min():.4f}..{kept_rmse.max():.4f}")

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert np.array_equal(df["id"].to_numpy(), ids)
f3 = df["f3"].fillna(0).to_numpy()
f1 = df["f1"].fillna(0).to_numpy()
f11 = df["f11"].fillna(0).to_numpy()
cat = df[["f6", "f7", "f8", "f9", "f10"]].fillna(0).sum(axis=1).to_numpy()
pu = np.load(ROOT / "scratchpad" / "tiebreak_signals.npz")["pu_hgb"].astype(np.float64)


def topset(v):
    s = pd.read_csv(ROOT / "data" / f"scores_{v}.csv").set_index("id")["score"].reindex(ids).to_numpy()
    m = np.zeros(len(s), bool)
    m[np.argpartition(-s, K)[:K]] = True
    return m


sets = {v: topset(v) for v in OBS}

# per-calibration predicted net for each probe pool (counts /1e5)
pool_nets = {}
for probe, base in PROBES:
    IN = sets[probe] & ~sets[base]
    OUT = sets[base] & ~sets[probe]
    nets = (masks[:, IN].sum(axis=1) - masks[:, OUT].sum(axis=1)) / 1e5
    pool_nets[(probe, base)] = nets
    print(f"   {probe}|{base}: swap {int(IN.sum()):,}  per-cal net med {np.median(nets)*1e5:+.0f} members")

L = 30.0 * kept_rmse ** 2                            # sum of squared residuals per calibration


def pit_values(eta, tau):
    w = np.exp(-eta * (L - L.min()) / (2 * (SIGMA ** 2 + tau ** 2)))
    w = w / w.sum()
    pits = []
    for probe, base in PROBES:
        mu_k = OBS[base] + pool_nets[(probe, base)]
        s_tot = np.sqrt(SIGMA ** 2 + tau ** 2)
        # mixture CDF at realized value
        from scipy.stats import norm
        pits.append(float((w * norm.cdf((OBS[probe] - mu_k) / s_tot)).sum()))
    return np.array(pits), w


best = None
for eta in (0.05, 0.1, 0.2, 0.4, 0.7, 1.0, 1.5, 2.5):
    for tau in (0.0005, 0.001, 0.002, 0.003, 0.004, 0.006):
        pits, w = pit_values(eta, tau)
        ks = float(np.max(np.abs(np.sort(pits) - (np.arange(1, 9) - 0.5) / 8)))
        if best is None or ks < best[0]:
            best = (ks, eta, tau, pits, w)
ks, eta, tau, pits, W = best
print(f"\ncalibration: eta*={eta}, tau*={tau} (KS {ks:.3f})")
print(f"  PIT of the 8 probes (want ~uniform): {[round(p, 2) for p in sorted(pits)]}")
uni, _ = pit_values(1.0, 0.0)
print(f"  [uncalibrated eta=1,tau=0 PITs: {[round(p, 2) for p in sorted(uni[0] if isinstance(uni, tuple) else uni)]}]")
np.save(ROOT / "scratchpad" / "ensemble_weights.npy", W)

mu = W @ masks                                        # calibrated member inclusion probs
print(f"  effective sample size of weights: {1.0 / float((W ** 2).sum()):.1f} of {Kc}")

# ---- B. eigen-probe designer ----
band = (mu > 0.02) & (mu < 0.98)
B = np.flatnonzero(band)
print(f"\nB. boundary band: {len(B):,} members (0.02 < mu < 0.98)")
X = (masks[:, B].astype(np.float64) - mu[B]) * np.sqrt(W)[:, None]
U, S_, Vt = np.linalg.svd(X, full_matrices=False)
evals = S_ ** 2
print(f"   covariance spectrum (top 6): {[round(float(e), 1) for e in evals[:6]]}")

banked = sets["v37L"]
whale = M_hist.all(axis=0)
specs = []
for k_ in range(3):
    v = Vt[k_]
    lo_g = ~banked[B] & (f3[B] == 0) & (f11[B] <= 0.10)
    hi_g = banked[B] & ~whale[B]
    order_pos = np.argsort(-v)
    order_neg = np.argsort(v)
    for m in (800, 1200, 1800, 2500):
        IN_i = B[order_pos[lo_g[order_pos]][:m]] if False else None
    # build pools: top-m positive components outside, top-m negative inside
    pos_idx = [i for i in order_pos if lo_g[i]][: 3000]
    neg_idx = [i for i in order_neg if hi_g[i]][: 3000]
    for m in (800, 1200, 1800, 2500):
        if m > min(len(pos_idx), len(neg_idx)):
            continue
        sel_in = B[np.array(pos_idx[:m])]
        sel_out = B[np.array(neg_idx[:m])]
        nets = (masks[:, sel_in].sum(axis=1) - masks[:, sel_out].sum(axis=1)) / 1e5
        mean_ = float((W * nets).sum())
        var_ = float((W * (nets - mean_) ** 2).sum())
        sd_counts = np.sqrt(var_) * 1e5
        if sd_counts >= 5 * SIGMA * 1e5 or m == 2500:
            eig_bits = 0.5 * np.log2(1 + var_ / (SIGMA ** 2 + tau ** 2))
            specs.append((k_ + 1, m, mean_, np.sqrt(var_), eig_bits, sel_in, sel_out))
            break
print("\n   eigen-probe specs (mode, N, E[net], sd(net), EIG bits):")
for kk, m, mean_, sd_, bits, sel_in, sel_out in specs:
    print(f"   mode {kk}: N={m:,}  E[net] {mean_*1e5:+.0f} members  sd {sd_*1e5:.0f}  "
          f"EIG {bits:.2f} bits  | IN: f1 med {np.median(f1[sel_in]):,.0f} cat {np.median(cat[sel_in]):,.0f}"
          f" | OUT: f1 med {np.median(f1[sel_out]):,.0f} cat {np.median(cat[sel_out]):,.0f}")
np.savez(ROOT / "scratchpad" / "eigenprobe_specs.npz",
         **{f"mode{kk}_in": si for kk, m, a, b, c, si, so in specs},
         **{f"mode{kk}_out": so for kk, m, a, b, c, si, so in specs})

# ---- C. v44 tranche, calibrated-predictive gate ----
print("\nC. v44 (v37L base, reweighted votes, pu-veto, cap 600):")
vote_w = mu                                            # calibrated probabilities
tbm = pd.Series(pu).rank(pct=True).to_numpy()
in_pool = np.flatnonzero(~banked & (f3 == 0))
out_pool = np.flatnonzero(banked & ~whale)
in_pool = in_pool[np.lexsort((-tbm[in_pool], -vote_w[in_pool]))]
out_pool = out_pool[np.lexsort((tbm[out_pool], vote_w[out_pool]))]
swap_in, swap_out, veto = [], [], 0
i = j = 0
while len(swap_in) < 600 and i < len(in_pool) and j < len(out_pool):
    a, b = in_pool[i], out_pool[j]
    if vote_w[a] - vote_w[b] < 0.5:
        break
    if pu[a] < pu[b]:
        veto += 1
        i += 1
        continue
    swap_in.append(a)
    swap_out.append(b)
    i += 1
    j += 1
print(f"   tranche N={len(swap_in)} (vetoed {veto})")
if swap_in:
    si, so = np.array(swap_in), np.array(swap_out)
    nets = (masks[:, si].sum(axis=1) - masks[:, so].sum(axis=1)) / 1e5
    mean_ = float((W * nets).sum())
    sd_ = float(np.sqrt((W * (nets - mean_) ** 2).sum() + SIGMA ** 2 + tau ** 2))
    from scipy.stats import norm
    p_beat = 1 - norm.cdf((0.918971 - (OBS["v37L"] + mean_)) / sd_)
    print(f"   calibrated predictive: E[read] {OBS['v37L'] + mean_:.4f}  sd {sd_:.4f}  "
          f"P(> banked 0.918971) {p_beat:.0%}")
    print(f"   IN: vote_w med {np.median(vote_w[si]):.2f} f1 {np.median(f1[si]):,.0f} cat {np.median(cat[si]):,.0f}"
          f" | OUT: vote_w med {np.median(vote_w[so]):.2f} f1 {np.median(f1[so]):,.0f} cat {np.median(cat[so]):,.0f}")
    np.savez(ROOT / "scratchpad" / "v44_pools.npz", swap_in=si, swap_out=so)
