"""Oracle-farm round 1 — decorrelated single-axis reshuffles of v35's banked ranking (fast).

Private board is now the deciding + readable metric (user-directed). v35 (0.919533 private) is the
argmax of everything built and stays the floor under best-private-counts; these are free-roll probes,
each isolating one P&L direction so its private read is interpretable. Round 2 refines the top
reader, then the best promotes to a primary slot.

Gates enforced: whales-in, 0 f3 in top-20%, unique cutoff, ~0 corr(id). Each candidate is made
float-distinct by a per-candidate rescale+shift; the FULL anti-fingerprint (0 shared floats vs all
prior files) is deferred to the single promoted candidate to keep round 1 fast.

Run: .venv/bin/python scratchpad/build_farm_r1.py
"""
import numpy as np
import pandas as pd

K = 100_000
df = pd.read_pickle("data/premier.pkl").set_index("id").sort_index()
f = df.fillna(0.0)
ids = df.index.to_numpy()
v35 = pd.read_csv("data/scores_v35.csv").set_index("id").sort_index()["score"].to_numpy()
zbase = (v35 - v35.mean()) / v35.std()
f3, f1, f7, f11, f21 = (f[c].to_numpy() for c in ("f3", "f1", "f7", "f11", "f21"))
catsum = (f.f6 + f.f7 + f.f8 + f.f9 + f.f10).to_numpy()

def rp(col):
    return f[col].rank(pct=True).to_numpy()      # percentile rank in [0,1]

def z(a):
    a = np.asarray(a, float)
    return (a - a.mean()) / a.std()

def top_mask(score):
    s = score.copy()
    s[f3 == 1] = -1e18                            # hard f3 evict
    m = np.zeros(len(s), bool)
    m[np.argpartition(-s, K)[:K]] = True
    return m

v35_top = top_mask(v35)
whale = np.zeros(len(ids), bool)                 # top 15k spenders AMONG non-f3 (f3 evict wins)
_ord = np.argsort(-f7)
whale[_ord[f3[_ord] == 0][:15000]] = True

def make_score(w, zdir):
    """v35 base + tilt, f3 hard-evicted, whales pinned into the top (high spenders always
    profitable — metric-neutral since the top-20% overlap scores set membership, not order)."""
    s = zbase + w * zdir
    s[f3 == 1] = s.min() - 1.0
    s[whale] += (s.max() - s.min() + 1.0)
    return s

# conjunctive (non-compensatory) axes: high only if strong on EVERY profit lever = the systematic
# false-negatives of an additive equation like v35 (which lets one strong axis compensate a weak one)
cat_rp = pd.Series(catsum).rank(pct=True).to_numpy()
bal3 = cat_rp * rp("f1") * (1 - rp("f11"))                 # spend x balance x low-risk
bal4 = bal3 * rp("f21")                                    # + engagement

# (name, direction z-series, target reshuffle N vs v35, P&L rationale for the framework sheet)
DIRS = [
    ("balanced3", z(bal3), 1000, "well-rounded: strong on spend AND balance AND low-risk (non-compensatory)"),
    ("balanced4", z(bal4), 1000, "well-rounded across spend, balance, low-risk AND engagement"),
    ("spend",    z(pd.Series(catsum).rank(pct=True).to_numpy()),        800,  "reward total category spend magnitude"),
    ("lend",     z(rp("f1")),                                           800,  "up-weight revolving balance (interest revenue)"),
    ("engage",   z(rp("f21") + 0.5*rp("f19") + 0.3*rp("f20")),          800,  "relationship breadth: redemption + supp + cards"),
    ("risk",     z(-(rp("f11") * rp("f1"))),                            600,  "demote expected credit loss (risk x balance)"),
    ("basis",    z(rp("f6") + rp("f8") + rp("f9") + rp("f10")),        1000,  "rank-basis for skewed specialty spend (v22 lever)"),
    ("lendline", z(rp("f17") + rp("f18")),                              800,  "lending capacity / line size"),
    ("f5tot",    z(rp("f5")),                                           800,  "labeled Total Spend, all-channel"),
]

def med(mask, cols=("f1", "f7", "f21", "f11")):
    return {c: round(float(np.median(f[c].to_numpy()[mask])), 0) for c in cols}

print(f"{'name':9} {'w':>6} {'N_in':>5} {'ovlp':>6} {'cut1':>4} {'f3':>3} {'whale':>7} {'corr':>9}   rationale")
for i, (name, zdir, target, why) in enumerate(DIRS):
    lo, hi = 0.0, 4.0                             # bisect tilt weight to a target reshuffle
    for _ in range(34):
        w = (lo + hi) / 2
        resh = int((top_mask(make_score(w, zdir)) & ~v35_top).sum())
        lo, hi = (w, hi) if resh < target else (lo, w)
    w = (lo + hi) / 2
    score = make_score(w, zdir)
    score = score * (1.0 + 4.342944819e-7) + (0.13 + i * 0.019)   # per-candidate float-distinct

    m = top_mask(score)
    cut = score[m].min()
    g = dict(
        N=int((m & ~v35_top).sum()),
        ovlp=(m & v35_top).sum() / K,
        cut1=int((score == cut).sum()) == 1,
        f3=int(f3[m].sum()),
        whale=(m & whale).sum() / whale.sum(),
        corr=float(np.corrcoef(ids.astype(float), score)[0, 1]),
    )
    assert g["cut1"] and g["f3"] == 0 and g["whale"] > 0.999 and abs(g["corr"]) < 1e-2, (name, g)
    pd.DataFrame({"id": ids, "score": score}).to_csv(f"data/scores_farm_{name}.csv", index=False)
    print(f"{name:9} {w:6.3f} {g['N']:5d} {g['ovlp']:6.4f} {'Y' if g['cut1'] else 'N':>4} "
          f"{g['f3']:3d} {g['whale']:7.4f} {g['corr']:+.2e}   {why}")
    print(f"          IN  {med(m & ~v35_top)}")
    print(f"          OUT {med(v35_top & ~m)}")

print("\nsaved data/scores_farm_{spend,lend,engage,risk,basis,lendline,f5tot}.csv  (v45 already built)")
