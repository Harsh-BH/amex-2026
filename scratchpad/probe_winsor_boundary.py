# A39 probe: winsor-cap plateau mass at v29's top-20% boundary (run 2026-07-02).
# Question: can within-plateau (pre-clip tail) reordering fund a >0.915 candidate?
# Answer: NO — band 90-110K holds only 194 f1-capped members (110 in / 84 out);
# >=1 value-feature-at-cap = 3,374 (1,626 in / 1,748 out, symmetric), concentrated
# on near-zero-truth-weight specialty spends; the 2,642 f1-capped members v29
# excludes are median rank 462,923, zero catspend, f11 0.150 = the v33-evicted
# distress profile. Oracle ceiling ~ +0.002-0.003 overlap.
import pandas as pd, numpy as np

df = pd.read_pickle("data/premier.pkl")
sc = pd.read_csv("data/scores_v29.csv")
scol = [c for c in sc.columns if c.lower() != "id"][0]
sc = sc.sort_values(scol, ascending=False).reset_index(drop=True)
sc["rank"] = np.arange(1, len(sc) + 1)
m = df.merge(sc[["id", "rank"]], on="id")

WINS = ["f1","f4","f5","f6","f7","f8","f9","f10","f11","f12","f17","f18","f21"]  # A35 winsorized set
top  = m["rank"] <= 100_000
band = (m["rank"] > 90_000) & (m["rank"] <= 110_000)
jin  = (m["rank"] > 90_000) & (m["rank"] <= 100_000)
jout = (m["rank"] > 100_000) & (m["rank"] <= 110_000)

capmask = {}
print(f"{'feat':>4} {'capval':>12} {'pop@cap':>8} {'top100K':>8} {'in90-100':>8} {'out100-110':>10}")
for f in WINS:
    at = m[f] == m[f].max()
    capmask[f] = at
    print(f"{f:>4} {m[f].max():>12.3f} {at.sum():>8} {(at&top).sum():>8} {(at&jin).sum():>8} {(at&jout).sum():>10}")

val = ["f1","f7","f8","f9","f10","f6","f4","f21","f17","f18"]  # revenue-side caps only
any_cap = np.zeros(len(m), bool)
for f in val:
    any_cap |= capmask[f].fillna(False).values
print("band >=1 value-cap:", (any_cap & band).sum(), "in:", (any_cap & jin).sum(), "out:", (any_cap & jout).sum())

f1cap = capmask["f1"].fillna(False).values
sub = m[f1cap & ~top.values]
print("f1-capped excluded: n=%d, median rank %.0f, f11 %.3f, catspend %.0f" % (
    len(sub), sub["rank"].median(), sub["f11"].median(),
    sub[["f6","f7","f8","f9","f10"]].fillna(0).sum(axis=1).median()))

# self-check: plateau masses must be ~2.5-3% of 500K per A35's winsor finding
assert 9_000 <= (m["f1"] == m["f1"].max()).sum() <= 16_000, "f1 plateau mass off — winsor decode changed?"
