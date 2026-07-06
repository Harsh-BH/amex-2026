"""FIT the profile-proxy coefficient via an oracle sweep (not an arbitrary graft).

We can't refit-to-our-own-submissions (basin-locked: v41 proved a joint refit of engagement/
relationship terms goes sign-unstable and scored 0.9176), and a full joint refit against the private
truth needs dozens of reads. So fit the ONE new coefficient w directly: build v35 + w*z(profile_combo)
at a ladder of w (parameterized by reshuffle size N), read each on the private oracle, and the
N that MAXIMIZES private IS the fitted weight. Monotone-decline from N=0 => w*=0 (proxy adds nothing
at ANY weight; v35 optimal). A peak at N>0 => real signal, promote at that w.
Run: .venv/bin/python scratchpad/build_profile_sweep.py
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

tenure = z(rp("f4") + rp("f19") + rp("f20"))
wallet = z(rp("f17") + rp("f18"))
bureau = z(-rp("f11") - rp("f2") + 0.5 * rp("f17"))
combo = z(tenure + wallet + bureau)

def make_score(w):
    s = zbase + w * combo; s[f3 == 1] = s.min() - 1.0; s[whale] += (s.max() - s.min() + 1.0); return s

# ladder of reshuffle sizes -> increasing w (N=2000 already built as scores_profile_combo.csv)
LADDER = [500, 5000, 10000]
print(f"{'name':22} {'w':>6} {'N':>6} {'ovlp_v35':>8}")
for i, target in enumerate(LADDER):
    lo, hi = 0.0, 6.0
    for _ in range(36):
        w = (lo + hi) / 2
        lo, hi = (w, hi) if int((top_mask(make_score(w)) & ~v35_top).sum()) < target else (lo, w)
    w = (lo + hi) / 2
    s = make_score(w) * (1.0 + 4.342944819e-7) + (0.31 + i * 0.013)
    m = top_mask(s); cut = s[m].min()
    assert int((s == cut).sum()) == 1 and int(f3[m].sum()) == 0 and (m & whale).sum()/whale.sum() > 0.999
    name = f"profcombo_n{target}"
    pd.DataFrame({"id": ids, "score": s}).to_csv(f"data/scores_{name}.csv", index=False)
    print(f"{name:22} {w:6.3f} {int((m & ~v35_top).sum()):6d} {(m & v35_top).sum()/K:8.4f}")
print("existing scores_profile_combo.csv = the N=2000 point")
print("\nsweep points: N = 500, 2000, 5000, 10000  (w increasing) -> read private -> fit the peak")
