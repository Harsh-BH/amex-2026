"""Boundary tie-break battery + RETRODICTION harness (new validation instrument).

Goal: find signals that discriminate WITHIN the dense boundary band — where v41 proved
profile-level swaps wash — to fold into v42's margin ordering as tie-breaks.

Validation: retrodiction against every historically MEASURED swap outcome. Each measured
pair (probe vs base) has known net accuracy = (r_in - r_out) from its pre-registered
arithmetic and realized read. A useful tie-break, evaluated as mean(signal | IN pool) -
mean(signal | OUT pool) in population percentile units, should predict those nets' signs.
Controls: fit6 margin (the incumbent orderer) and a seeded random signal.

Candidates:
  pu_hgb    - PU-style classifier (HistGradientBoosting, NaN-native): certain-positives
              (members in ALL 28 top sets + 25/25 old-posterior vote) vs certain-negatives
              (never in any top set), scored on everyone. Nonlinear resemblance-to-core.
  pu_logit  - same labels, logistic on z-scored 0-filled features (linear control for pu_hgb)
  f5_rank   - raw f5 percentile (the non-circular tilt found in the miss profile)
  eng_blend - rank-mean of (f4, f22) (engagement, the v41-measured near-parity axis)
  dual_post - 0.5*vote15 + 0.5*voteCL (both posteriors' agreement)
  margin    - fit6 margin percentile (control: the orderer the swaps already used)
  random    - seeded noise (floor)
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parent.parent
K = 100_000
RNG = np.random.default_rng(19)

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
M = z["M"]
keys = [str(x) for x in z["obs_keys"]]
names = [str(x) for x in z["names"]]
print(f"cache: {M.shape[0]} masks")

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert np.array_equal(df["id"].to_numpy(), z["ids"])
ids = df["id"].to_numpy()

v15 = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy").sum(0) / 25.0
vCL = np.load(ROOT / "scratchpad" / "tri3_posterior_masks.npy").sum(0) / 4.0
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
SIX = [names.index(n) for n in ("z1", "z7", "z9", "z10", "exl", "f3neg")]
margin = (z["T"][:, SIX] @ w6.astype(np.float32)).astype(np.float64)


def topset(v):
    s = pd.read_csv(ROOT / "data" / f"scores_{v}.csv").set_index("id")["score"].reindex(ids).to_numpy()
    m = np.zeros(len(s), bool)
    m[np.argpartition(-s, K)[:K]] = True
    return m


# --- PU-style classifier: certain-positives vs certain-negatives ---
whale = M.all(axis=0)
pos = whale | ((v15 == 1.0) & topset("v35"))
neg_pool = np.flatnonzero(~M.any(axis=0))
neg = np.zeros(len(df), bool)
neg[RNG.choice(neg_pool, size=min(150_000, len(neg_pool)), replace=False)] = True
print(f"PU training: positives {int(pos.sum()):,}  negatives {int(neg.sum()):,}")

FEATS = [f"f{i}" for i in range(1, 24) if i != 3]          # f3 is a screen, not a signal
X = df[FEATS].to_numpy(np.float64)                          # NaN-native for HGB
y_idx = np.flatnonzero(pos | neg)
sub = RNG.choice(y_idx, size=min(200_000, len(y_idx)), replace=False)
hgb = HistGradientBoostingClassifier(max_iter=150, random_state=42)
hgb.fit(X[sub], pos[sub].astype(int))
pu_hgb = hgb.predict_proba(X)[:, 1]
print("pu_hgb fitted")

Xz = np.nan_to_num(X)
Xz = (Xz - Xz.mean(0)) / (Xz.std(0) + 1e-9)
from sklearn.linear_model import LogisticRegression  # noqa: E402
lg = LogisticRegression(max_iter=300, C=0.5)
lg.fit(Xz[sub], pos[sub].astype(int))
pu_logit = lg.decision_function(Xz)
print("pu_logit fitted")


def pr(v):
    return pd.Series(v).rank(pct=True).to_numpy()


SIGNALS = {
    "pu_hgb": pr(pu_hgb),
    "pu_logit": pr(pu_logit),
    "f5_rank": pr(df["f5"].fillna(0).to_numpy()),
    "eng_blend": (pr(df["f4"].fillna(0).to_numpy()) + pr(df["f22"].fillna(0).to_numpy())) / 2,
    "dual_post": pr(0.5 * v15 + 0.5 * vCL),
    "margin_CTRL": pr(margin),
    "random_CTRL": pr(RNG.standard_normal(len(df))),
}

# --- measured swap pairs: (probe, base, measured net accuracy r_in - r_out) ---
PAIRS = [("v33", "v29", -0.611), ("v34", "v29", +0.50), ("v35", "v34", +0.074),
         ("v36", "v35", -0.252), ("v37L", "v35", +0.034), ("v30", "v29", -0.310),
         ("v41", "v35", -0.076)]

sets = {v: topset(v) for v in {p for pair in PAIRS for p in pair[:2]}}
print(f"\nretrodiction: pred = mean(sig|IN) - mean(sig|OUT), population-percentile units")
header = f"{'pair':>12} {'n_swap':>7} {'net':>7} |" + "".join(f"{s:>12}" for s in SIGNALS)
print(header)
preds = {s: [] for s in SIGNALS}
nets = []
for probe, base, net in PAIRS:
    IN = sets[probe] & ~sets[base]
    OUT = sets[base] & ~sets[probe]
    nets.append(net)
    row = f"{probe + '|' + base:>12} {int(IN.sum()):>7,} {net:>+7.3f} |"
    for s, sig in SIGNALS.items():
        d = float(sig[IN].mean() - sig[OUT].mean())
        preds[s].append(d)
        row += f"{d:>+12.3f}"
    print(row)

from scipy.stats import spearmanr  # noqa: E402
print(f"\n{'signal':>12} {'sign-hits':>10} {'spearman':>9}")
nets_a = np.array(nets)
for s in SIGNALS:
    p = np.array(preds[s])
    hits = int((np.sign(p) == np.sign(nets_a)).sum())
    rho = spearmanr(p, nets_a).statistic
    print(f"{s:>12} {hits:>7}/7 {rho:>+9.3f}")

np.savez_compressed(ROOT / "scratchpad" / "tiebreak_signals.npz",
                    **{k: v.astype(np.float32) for k, v in SIGNALS.items()})
print("\nsaved scratchpad/tiebreak_signals.npz")
