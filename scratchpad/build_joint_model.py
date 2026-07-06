"""Full-feature JOINT model (from scratch, not a tilt on v35). All P&L features + the profile-driver
proxies (tenure/wallet/bureau/engagement) as first-class terms; economics-set core weights; sweep the
profile-block weight lambda. lambda=0 => fresh full-feature P&L baseline (does a fresh economics core
match the LB-validated v35?); lambda>0 => profile drivers weighted up. Read private -> dose-response.

Core weights are economics-grounded + the LB lesson (lending fat-margin dominant, interchange thin):
  +0.70 z(revolve f1)  +0.45 z(spend)  -0.35 z(risk f11)  -0.30 z(exp-loss f11*f1)
  -0.12 z(redeem f21)  -0.10 z(benefit)  -0.05 z(attrition f2);  f3 hard-evict.
Run: .venv/bin/python scratchpad/build_joint_model.py
"""
import numpy as np, pandas as pd

K = 100_000
df = pd.read_pickle("data/premier.pkl").set_index("id").sort_index(); f = df.fillna(0.0)
ids = df.index.to_numpy()
v35 = pd.read_csv("data/scores_v35.csv").set_index("id").sort_index()["score"].to_numpy()
v35_top = np.zeros(len(ids), bool); v35_top[np.argpartition(-v35, K)[:K]] = True
f3, f7 = f.f3.to_numpy(), f.f7.to_numpy()
rp = lambda c: f[c].rank(pct=True).to_numpy()
z = lambda a: (np.asarray(a, float) - np.asarray(a, float).mean()) / np.asarray(a, float).std()
whale = np.zeros(len(ids), bool); wo = np.argsort(-f7); whale[wo[f3[wo] == 0][:15000]] = True

f1, f11, f2, f21 = f.f1.to_numpy(), f.f11.to_numpy(), f.f2.to_numpy(), f.f21.to_numpy()
catsum = f[["f6","f7","f8","f9","f10"]].sum(axis=1).to_numpy()
spend = np.where(catsum > 0, catsum, f.f5.to_numpy())               # f5-fallback
benefit = 50*f.f13.to_numpy() + f.f14.to_numpy() + 15*f.f15.to_numpy() + f.f16.to_numpy()

# --- CORE P&L (fresh, economics + LB lending-led) ---
core = (0.70*z(f1) + 0.45*z(spend) - 0.35*z(f11) - 0.30*z(f11*f1)
        - 0.12*z(rp("f21")) - 0.10*z(rp("f13")+rp("f14")+rp("f15")+rp("f16")) - 0.05*z(rp("f2")))
# --- PROFILE block (the absent drivers, joined) ---
tenure = z(rp("f4") + rp("f19") + rp("f20"))
wallet = z(rp("f17") + rp("f18"))
bureau = z(-rp("f11") - rp("f2") + 0.5*rp("f17"))
engage = z(rp("f12") + rp("f22") + rp("f23"))
profile = z(tenure + wallet + bureau + engage)

def finalize(name, raw, i):
    s = raw.astype(float).copy(); s[f3 == 1] = s.min() - 1.0; s[whale] += (s.max() - s.min() + 1.0)
    s = s * (1.0 + 4.342944819e-7) + (0.41 + i*0.011)
    m = np.zeros(len(s), bool); m[np.argpartition(-s, K)[:K]] = True
    cut = s[m].min()
    assert int((s == cut).sum()) == 1 and int(f3[m].sum()) == 0 and (m & whale).sum()/whale.sum() > 0.999
    pd.DataFrame({"id": ids, "score": s}).to_csv(f"data/scores_{name}.csv", index=False)
    print(f"  {name:16} ovlp_v35 {(m & v35_top).sum()/K:.4f}")

print("full-feature joint model, sweeping profile weight lambda:")
for i, lam in enumerate([0.0, 0.5, 1.0, 2.0]):
    finalize(f"joint_lam{str(lam).replace('.','p')}", z(core) + lam*profile, i)
print("\nlambda=0 = fresh full-feature P&L baseline; higher lambda = profile drivers weighted up")
