"""Proxy the absent "Profile" truth-drivers (Tenure, Size-of-Wallet, Bureau score) from f1-f23 and
test as bounded tilts on v35. The PDF shows Amex computed profitability using these Profile
attributes, but only Riskiness (f11) was shared; Tenure/Wallet/Bureau are absent. A proxy is a
FUNCTION of f1-f23 -> mathematically a re-weighting we've largely mapped, so odds are low; but these
specific constructions target the known drivers and are oracle-validated. Whale-guarded, f3-evict,
unique cutoff, float-distinct. Run: .venv/bin/python scratchpad/build_profile_proxy.py
"""
import numpy as np, pandas as pd

K = 100_000
df = pd.read_pickle("data/premier.pkl").set_index("id").sort_index(); f = df.fillna(0.0)
ids = df.index.to_numpy()
v35 = pd.read_csv("data/scores_v35.csv").set_index("id").sort_index()["score"].to_numpy()
zbase = (v35 - v35.mean()) / v35.std()
f3, f7 = f.f3.to_numpy(), f.f7.to_numpy()
rp = lambda c: f[c].rank(pct=True).to_numpy()
z = lambda a: (np.asarray(a, float) - np.asarray(a, float).mean()) / np.asarray(a, float).std()

def top_mask(s):
    x = s.copy(); x[f3 == 1] = -1e18
    m = np.zeros(len(x), bool); m[np.argpartition(-x, K)[:K]] = True; return m
v35_top = top_mask(v35)
whale = np.zeros(len(ids), bool); wo = np.argsort(-f7); whale[wo[f3[wo] == 0][:15000]] = True

def make_score(w, zdir):
    s = zbase + w * zdir; s[f3 == 1] = s.min() - 1.0; s[whale] += (s.max() - s.min() + 1.0); return s

# --- absent-Profile-driver proxies (all functions of f1-f23) ---
tenure = z(rp("f4") + rp("f19") + rp("f20"))              # relationship maturity/depth
wallet = z(rp("f17") + rp("f18"))                          # credit capacity = wallet size
bureau = z(-rp("f11") - rp("f2") + 0.5 * rp("f17"))        # behavior/creditworthiness score
combo = z(tenure + wallet + bureau)
DIRS = [("tenure_depth", tenure, 1500), ("wallet_cap", wallet, 1500),
        ("bureau_qual", bureau, 1500), ("profile_combo", combo, 2000)]

def med(mask, cols=("f4", "f17", "f11", "f19")):
    return {c: round(float(np.median(f[c].to_numpy()[mask])), 0) for c in cols}

print(f"{'name':14} {'w':>6} {'N':>5} {'ovlp':>6} {'cut1':>4} {'f3':>3} {'whale':>7}")
for i, (name, zdir, target) in enumerate(DIRS):
    lo, hi = 0.0, 4.0
    for _ in range(34):
        w = (lo + hi) / 2
        lo, hi = (w, hi) if int((top_mask(make_score(w, zdir)) & ~v35_top).sum()) < target else (lo, w)
    w = (lo + hi) / 2
    s = make_score(w, zdir) * (1.0 + 4.342944819e-7) + (0.11 + i * 0.017)
    m = top_mask(s); cut = s[m].min()
    g = dict(N=int((m & ~v35_top).sum()), ovlp=(m & v35_top).sum()/K, cut1=int((s == cut).sum()) == 1,
             f3=int(f3[m].sum()), whale=(m & whale).sum()/whale.sum(),
             corr=float(np.corrcoef(ids.astype(float), s)[0, 1]))
    assert g["cut1"] and g["f3"] == 0 and g["whale"] > 0.999 and abs(g["corr"]) < 1e-2, (name, g)
    pd.DataFrame({"id": ids, "score": s}).to_csv(f"data/scores_{name}.csv", index=False)
    print(f"{name:14} {w:6.3f} {g['N']:5d} {g['ovlp']:6.4f} {'Y' if g['cut1'] else 'N':>4} {g['f3']:3d} {g['whale']:7.4f}")
    print(f"               IN  {med(m & ~v35_top)}   OUT {med(v35_top & ~m)}")
print("\nsaved scores_{tenure_depth,wallet_cap,bureau_qual,profile_combo}.csv")
