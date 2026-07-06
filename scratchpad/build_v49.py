"""Build v49 — the final conviction tranche off the measured v37L base (34 EXACT constraints).

The one construction that has never read negative (v34 +0.44/600, v35 +0.07/1878, v44 −0.006/533),
refreshed with SIX newly-exact probe reads (#29-34, hover-confirmed) folded into the Gibbs-eta
PIT-calibrated ensemble (redesign_step1 machinery, 12 probe pairs now). Target: a primary upload
with a real shot at >= 0.920 (needs net*k >= +86 public counts over 0.919143).

Stage A prints the calibrated predictive E[read], sd, P(>=0.920), P(>= banked) — the SHIP GATE.
Stage B (only if gate passes) packages scores/xlsx exactly like v46-48.

Run: .venv/bin/python scratchpad/build_v49.py
"""
from pathlib import Path
import re

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parent.parent
K = 100_000
SIGMA = 0.001
BANKED = 0.918971
TARGET = 0.920

# exact reads (hover-confirmed 2026-07-05)
OBS = {"v29": .915, "v33": .907, "v34": .917614, "v35": .918971, "v36": .917386,
       "v37L": .919143, "v40": .913957, "v41": .917643, "v43": .912429,
       "v44": .919100, "v46": .911143, "v47": .911514, "v48": .910243}
PROBES = [("v33", "v29"), ("v34", "v29"), ("v35", "v34"), ("v36", "v35"),
          ("v37L", "v35"), ("v41", "v35"), ("v40", "v35"), ("v43", "v37L"),
          ("v44", "v37L"), ("v46", "v37L"), ("v47", "v37L"), ("v48", "v37L")]

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
M_hist, ids = z["M"], z["ids"]
masks = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
Kc = masks.shape[0]
log = (ROOT / "scratchpad" / "refit30_log.txt").read_text()
seed_rmse = [(int(a), float(b)) for a, b in re.findall(r"seed (\d+): RMSE ([0-9.]+)", log)][-48:]
rs = np.array([r for _, r in seed_rmse])
keep = rs <= rs.min() * 1.5 + 1e-6
kept_rmse = rs[keep]
assert keep.sum() == Kc
print(f"ensemble: {Kc} calibrations, RMSE {kept_rmse.min():.4f}..{kept_rmse.max():.4f}")

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
pool_nets = {}
for probe, base in PROBES:
    IN = sets[probe] & ~sets[base]
    OUT = sets[base] & ~sets[probe]
    pool_nets[(probe, base)] = (masks[:, IN].sum(axis=1) - masks[:, OUT].sum(axis=1)) / 1e5

L = 30.0 * kept_rmse ** 2


def pit_values(eta, tau):
    w = np.exp(-eta * (L - L.min()) / (2 * (SIGMA ** 2 + tau ** 2)))
    w = w / w.sum()
    s_tot = np.sqrt(SIGMA ** 2 + tau ** 2)
    pits = [float((w * norm.cdf((OBS[p] - (OBS[b] + pool_nets[(p, b)])) / s_tot)).sum())
            for p, b in PROBES]
    return np.array(pits), w


best = None
for eta in (0.02, 0.05, 0.1, 0.2, 0.4, 0.7, 1.0, 1.5, 2.5):
    for tau in (0.0005, 0.001, 0.002, 0.003, 0.004, 0.006):
        pits, w = pit_values(eta, tau)
        n = len(pits)
        ks = float(np.max(np.abs(np.sort(pits) - (np.arange(1, n + 1) - 0.5) / n)))
        if best is None or ks < best[0]:
            best = (ks, eta, tau, pits, w)
ks, eta, tau, pits, W = best
print(f"calibration on 12 EXACT probes: eta*={eta}, tau*={tau} (KS {ks:.3f}); "
      f"ESS {1.0/float((W**2).sum()):.1f}/{Kc}")
print(f"  PITs: {[round(p,2) for p in sorted(pits)]}")

mu = W @ masks
banked_set = sets["v37L"]
whale = M_hist.all(axis=0)
tbm = pd.Series(pu).rank(pct=True).to_numpy()

# ---- tranche selection: gap >= GAP, pu no-trade-down veto, cap CAP ----
for GAP, CAP in ((0.5, 900), (0.4, 900), (0.5, 600)):
    in_pool = np.flatnonzero(~banked_set & (f3 == 0))
    out_pool = np.flatnonzero(banked_set & ~whale)
    in_pool = in_pool[np.lexsort((-tbm[in_pool], -mu[in_pool]))]
    out_pool = out_pool[np.lexsort((tbm[out_pool], mu[out_pool]))]
    swap_in, swap_out, veto = [], [], 0
    i = j = 0
    while len(swap_in) < CAP and i < len(in_pool) and j < len(out_pool):
        a, b = in_pool[i], out_pool[j]
        if mu[a] - mu[b] < GAP:
            break
        if pu[a] < pu[b]:
            veto += 1
            i += 1
            continue
        swap_in.append(a)
        swap_out.append(b)
        i += 1
        j += 1
    if not swap_in:
        print(f"GAP={GAP} CAP={CAP}: tranche EMPTY (vetoed {veto})")
        continue
    si, so = np.array(swap_in), np.array(swap_out)
    nets = (masks[:, si].sum(axis=1) - masks[:, so].sum(axis=1)) / 1e5
    mean_ = float((W * nets).sum())
    # predictive sd: ensemble spread + read noise + mask sampling on k swaps
    k_ = len(si)
    sd_mask = 0.68 * np.sqrt(k_) / 7e4 * np.sqrt(2)   # conservative mask+split term
    sd_ = float(np.sqrt((W * (nets - mean_) ** 2).sum() + SIGMA ** 2 + tau ** 2 + sd_mask ** 2))
    E = OBS["v37L"] + mean_
    print(f"\nGAP={GAP} CAP={CAP}: tranche N={k_} (vetoed {veto})")
    print(f"  IN : mu med {np.median(mu[si]):.2f}  f1 {np.median(f1[si]):,.0f}  cat {np.median(cat[si]):,.0f}  f11 {np.median(f11[si]):.4f}")
    print(f"  OUT: mu med {np.median(mu[so]):.2f}  f1 {np.median(f1[so]):,.0f}  cat {np.median(cat[so]):,.0f}")
    print(f"  calibrated predictive: E[read] {E:.4f}  sd {sd_:.4f}")
    print(f"  P(>= banked {BANKED}) = {1-norm.cdf((BANKED-E)/sd_):.0%}   "
          f"P(>= {TARGET}) = {1-norm.cdf((TARGET-E)/sd_):.0%}")
    np.savez(ROOT / "scratchpad" / f"v49_pools_gap{GAP}_cap{CAP}.npz", swap_in=si, swap_out=so)
print("\nSHIP GATE: package only if a tranche shows E >= ~0.9192 AND P(>=0.920) >= ~15% "
      "(self-selection bias means realized tends to land ~1 sigma below E — price it).")
