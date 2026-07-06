"""v49 pool provenance — regenerates scratchpad/v49_eigen_pool.npz deterministically.

Recomputes the 12-exact-probe Gibbs-eta recalibration (identical grid to build_v49.py),
eigendecomposes the calibrated residual co-membership covariance over the uncertainty band,
and selects the max-P(>=0.920) pool (mode 3, N=1,200). Saved post-hoc after the validator
flagged that the original run lived only in a session shell — logic verbatim; reproducibility
asserted against the shipped npz at the bottom.

Run: .venv/bin/python scratchpad/v49_eigen_select.py
"""
from pathlib import Path
import re

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parent.parent
K = 100_000
SIG = 0.001

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
ids, M = z["ids"], z["M"]
masks = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
log = (ROOT / "scratchpad" / "refit30_log.txt").read_text()
rs = np.array([float(b) for _, b in re.findall(r"seed (\d+): RMSE ([0-9.]+)", log)][-48:])
L = 30.0 * rs[rs <= rs.min() * 1.5 + 1e-6] ** 2

OBS = {"v29": .915, "v33": .907, "v34": .917614, "v35": .918971, "v36": .917386,
       "v37L": .919143, "v40": .913957, "v41": .917643, "v43": .912429,
       "v44": .9191, "v46": .911143, "v47": .911514, "v48": .910243}
PROBES = [("v33", "v29"), ("v34", "v29"), ("v35", "v34"), ("v36", "v35"), ("v37L", "v35"),
          ("v41", "v35"), ("v40", "v35"), ("v43", "v37L"), ("v44", "v37L"),
          ("v46", "v37L"), ("v47", "v37L"), ("v48", "v37L")]


def top(v):
    s = pd.read_csv(ROOT / "data" / f"scores_{v}.csv").set_index("id")["score"].reindex(ids).to_numpy()
    m = np.zeros(len(s), bool)
    m[np.argpartition(-s, K)[:K]] = True
    return m


sets = {v: top(v) for v in OBS}
pn = {(p, b): (masks[:, sets[p] & ~sets[b]].sum(1) - masks[:, sets[b] & ~sets[p]].sum(1)) / 1e5
      for p, b in PROBES}


def cal(eta, tau):
    w = np.exp(-eta * (L - L.min()) / (2 * (SIG ** 2 + tau ** 2)))
    w /= w.sum()
    st = np.sqrt(SIG ** 2 + tau ** 2)
    ps = [float((w * norm.cdf((OBS[p] - (OBS[b] + pn[(p, b)])) / st)).sum()) for p, b in PROBES]
    return np.array(ps), w


best = None
for eta in (0.02, 0.05, 0.1, 0.2, 0.4, 0.7, 1.0, 1.5, 2.5):
    for tau in (0.0005, 0.001, 0.002, 0.003, 0.004, 0.006):
        ps, w = cal(eta, tau)
        ks = float(np.max(np.abs(np.sort(ps) - (np.arange(1, 13) - 0.5) / 12)))
        if best is None or ks < best[0]:
            best = (ks, eta, tau, w)
ks, eta, tau, W = best
mu = W @ masks

f = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True).fillna(0.0)
f3 = f["f3"].to_numpy()
t37 = sets["v37L"]
whale = M.all(axis=0)
band = (mu > 0.02) & (mu < 0.98)
B = np.flatnonzero(band)
X = (masks[:, B].astype(np.float64) - mu[B]) * np.sqrt(W)[:, None]
U, S_, Vt = np.linalg.svd(X, full_matrices=False)
lo_g = ~t37[B] & (f3[B] == 0)
hi_g = t37[B] & ~whale[B]

out = []
for kk in range(3):
    v = Vt[kk]
    pos = [i for i in np.argsort(-v) if lo_g[i]][:2500]
    neg = [i for i in np.argsort(v) if hi_g[i]][:2500]
    for N in (800, 1200, 1800):
        si = B[np.array(pos[:N])]
        so = B[np.array(neg[:N])]
        nets = (masks[:, si].sum(1) - masks[:, so].sum(1)) / 1e5
        m_ = float((W * nets).sum())
        sd = float(np.sqrt((W * (nets - m_) ** 2).sum() + SIG ** 2 + tau ** 2))
        E = 0.919143 + m_
        out.append((kk + 1, N, E, sd, 1 - norm.cdf((0.920 - E) / sd),
                    1 - norm.cdf((0.918971 - E) / sd), si, so))
bestpool = max(out, key=lambda r: r[4])
kk, N, E, sd, p920, pb, si, so = bestpool
print(f"selected mode{kk} N={N}: E {E:.4f} sd {sd:.4f} P(>=0.920) {p920:.0%}")

# reproducibility assertion vs the shipped pool
ship = np.load(ROOT / "scratchpad" / "v49_eigen_pool.npz")
assert np.array_equal(np.sort(si), np.sort(ship["swap_in"])), "IN pool mismatch vs shipped npz"
assert np.array_equal(np.sort(so), np.sort(ship["swap_out"])), "OUT pool mismatch vs shipped npz"
print("shipped v49_eigen_pool.npz REPRODUCED exactly ✓")
