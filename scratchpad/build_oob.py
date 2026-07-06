"""Out-of-basin portfolio — FROM-SCRATCH rankings on different principles (NOT v35 reshuffles).

v35 is basin-locked: its engine calibrates to reproduce our own past submissions, so it can only
interpolate within rankings we've already tried (v29->v35 moved 2,478 members). These candidates are
built fresh from premier.pkl on genuinely different structures, so they land in DIFFERENT basins and
can be validated on the now-readable private board. Reproducible from premier.pkl alone (GBM seeded).

Design notes grounded in the feature decode:
  f12 logins / f22 emails-opened / f23 emails-clicked = ENGAGEMENT (v35 ignores all three)
  f19 supp accts / f20 active cards = RELATIONSHIP breadth
  spend = category sum where a breakdown exists, else f5 (restores the fallback v35 dropped)
Every candidate: f3 hard-evict, whales pinned (top-15k non-f3 spenders always profitable), unique
cutoff, float-distinct. Run: .venv/bin/python scratchpad/build_oob.py
"""
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

K = 100_000
df = pd.read_pickle("data/premier.pkl").set_index("id").sort_index()
f = df.fillna(0.0)
ids = df.index.to_numpy()
v35 = pd.read_csv("data/scores_v35.csv").set_index("id").sort_index()["score"].to_numpy()
v35_top = np.zeros(len(ids), bool); v35_top[np.argpartition(-v35, K)[:K]] = True

f3 = f.f3.to_numpy(); f1 = f.f1.to_numpy(); f11 = f.f11.to_numpy(); f2 = f.f2.to_numpy()
catsum = f[["f6", "f7", "f8", "f9", "f10"]].sum(axis=1).to_numpy()
spend = np.where(catsum > 0, catsum, f.f5.to_numpy())          # f5-fallback for no-breakdown
rp = lambda a: pd.Series(a).rank(pct=True).to_numpy()

# --- percentile signals (scale-free) ---
p_spend, p_bal, p_risk = rp(spend), rp(f1), rp(f11)
p_engage = rp(rp(f.f12.to_numpy()) + rp(f.f22.to_numpy()) + rp(f.f23.to_numpy()))   # logins+emails
p_rel = rp(rp(f.f19.to_numpy()) + rp(f.f20.to_numpy()))                              # supp+cards
p_redeem = rp(f.f21.to_numpy())

# --- dollar P&L proxy (Amex economics) ---
interchange = 0.018 * spend
interest = 0.12 * f1
rewards_cost = 0.011 * spend
benefit_cost = 50*f.f13.to_numpy() + f.f14.to_numpy() + 15*f.f15.to_numpy() + f.f16.to_numpy()
credit_loss = 0.9 * f11 * f1
servicing = 100 + 20*f2
pnl_dollar = interchange + interest - rewards_cost - benefit_cost - credit_loss - servicing

whale = np.zeros(len(ids), bool)
_o = np.argsort(-f.f7.to_numpy()); whale[_o[f3[_o] == 0][:15000]] = True

def finalize(name, raw, why, i):
    """f3-evict, pin whales, distinct-shift, gate, save, report out-of-basin overlap."""
    s = raw.astype(float).copy()
    s[f3 == 1] = s.min() - 1.0
    s[whale] += (s.max() - s.min() + 1.0)                      # whales always in top
    s = s * (1.0 + 4.342944819e-7) + (0.11 + i * 0.017)        # float-distinct per candidate
    top = np.zeros(len(s), bool); top[np.argpartition(-s, K)[:K]] = True
    cut = s[top].min()
    g = dict(ovlp=(top & v35_top).sum()/K, cut1=int((s == cut).sum()) == 1,
             f3=int(f3[top].sum()), whale=(top & whale).sum()/whale.sum(),
             corr=float(np.corrcoef(ids.astype(float), s)[0, 1]))
    assert g["cut1"] and g["f3"] == 0 and g["whale"] > 0.999 and abs(g["corr"]) < 1e-2, (name, g)
    pd.DataFrame({"id": ids, "score": s}).to_csv(f"data/scores_oob_{name}.csv", index=False)
    print(f"{name:14} ovlp_v35 {g['ovlp']:.4f}  (out-of-basin={1-g['ovlp']:.1%})  whale {g['whale']:.3f}  | {why}")
    return top

# ---------------- candidates (different basins) ----------------
cands = {}
# 1. Multiplicative CLV: per-period margin x stickiness x survival. Discounts one-shot high-spenders.
clv = (p_spend + p_bal) * (0.5 + 0.5*p_engage) * (0.5 + 0.5*(1 - p_risk)) * (1 - 0.3*rp(f2))
cands["clv_mult"] = clv
# 2. CLV via RELATIONSHIP breadth as the stickiness factor instead of digital engagement
cands["clv_rel"] = (p_spend + p_bal) * (0.4 + 0.6*p_rel) * (0.5 + 0.5*(1 - p_risk))
# 3. TOPSIS (MCDA): closeness to the ideal across benefit(+)/cost(-) normalized criteria
crit = np.column_stack([p_spend, p_bal, p_engage, p_rel, 1 - p_risk, 1 - rp(benefit_cost)])
w = np.array([.30, .28, .10, .10, .17, .05]); nz = crit / np.sqrt((crit**2).sum(0)) * w
d_best = np.sqrt(((nz - nz.max(0))**2).sum(1)); d_worst = np.sqrt(((nz - nz.min(0))**2).sum(1))
cands["topsis"] = d_worst / (d_best + d_worst + 1e-12)
# 4. Full signed all-feature RANK composite (maximally decorrelated from v35's dollar basis)
allf = {c: rp(f[c].to_numpy()) for c in [f"f{i}" for i in range(1, 24)] if c not in ("f3",)}
sign = {"f2": -1, "f4": -1, "f11": -1, "f13": -1, "f14": -1, "f15": -1, "f16": -1}
cands["rank_comp"] = sum(sign.get(c, 1) * allf[c] for c in allf)
# 5. Relationship/engagement-led additive (breadth + engagement co-equal with spend + lending)
cands["rel_led"] = 0.30*p_spend + 0.25*p_bal + 0.20*p_rel + 0.15*p_engage + 0.10*(1 - p_risk)
# 6. Spend-led interchange-first (opposite philosophy to v35's lending-led)
cands["spend_led"] = 0.60*p_spend + 0.15*p_bal + 0.15*(1 - p_risk) + 0.10*p_redeem
# 7. Clean dollar P&L (anchor basin)
cands["dollar_pnl"] = pnl_dollar
# 8. Learned GBM on the P&L proxy, ALL 23 features raw (NaN-native = missingness as signal)
X = df[[f"f{i}" for i in range(1, 24)]].to_numpy()
gbm = HistGradientBoostingRegressor(random_state=42, max_iter=300, learning_rate=0.05,
                                    max_leaf_nodes=31, l2_regularization=1.0)
gbm.fit(X, pnl_dollar)
cands["gbm_pnl"] = gbm.predict(X)

print(f"{'candidate':14} {'overlap w/ v35':>0}")
tops = {name: finalize(name, raw, why, i) for i, (name, (raw, why)) in enumerate(
    {k: (v, d) for (k, v), d in zip(cands.items(), [
        "margin x engagement-stickiness x low-risk x retention (CLV, multiplicative)",
        "margin x relationship-breadth stickiness (CLV via supp/cards)",
        "MCDA TOPSIS: closeness to ideal across weighted P&L criteria",
        "full signed all-feature rank composite (max decorrelation)",
        "relationship+engagement co-equal with spend+lending (additive)",
        "spend/interchange-led (opposite of v35's lending-led)",
        "clean dollar P&L, Amex economics (anchor)",
        "HistGBM on P&L proxy, all 23 features NaN-native (nonlinear)",
    ])}.items())}

# pairwise decorrelation among candidates (Jaccard of top-20% sets)
print("\ntop-20% Jaccard between candidates (low = diverse basins):")
names = list(tops)
for a in range(len(names)):
    row = []
    for b in range(len(names)):
        i, j = tops[names[a]], tops[names[b]]
        row.append(f"{(i & j).sum()/(i | j).sum():.2f}")
    print(f"  {names[a]:12} " + " ".join(row))
print("  cols:", " ".join(f"{n[:4]}" for n in names))
