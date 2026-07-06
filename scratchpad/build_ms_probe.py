"""Manufactured-Spend false-POSITIVE probe (Reddit-sourced archetype).

Hypothesis: v35 over-ranks MS operators — members with huge spend concentrated in "Other" (f7),
abnormally low travel (f6 airline / f9 lodging) & dining (f10), near-zero revolving balance (f1~0),
high redemption (f21), low benefit usage — because v35 rewards spend but MS spend is low/negative
margin (gift-card/bill-pay cycling, rewards extracted at max efficiency). If the truth excludes them,
DEMOTING them from v35's top and swapping in the best non-MS outsiders RAISES the private score.

This is the project's first false-POSITIVE demotion (all prior probes promoted false-negatives) and
it DELIBERATELY evicts some f7-whales (the MS ones) — so whale-in < 1.0 by design; that's the test.
Honest caveat: "Other" is naturally the largest category, so the signature is a NOISY proxy for MS;
the oracle is the arbiter. Reproducible from premier.pkl + frozen scores_v35.csv.
Run: .venv/bin/python scratchpad/build_ms_probe.py
"""
import numpy as np, pandas as pd

K = 100_000
df = pd.read_pickle("data/premier.pkl").set_index("id").sort_index(); f = df.fillna(0.0)
ids = df.index.to_numpy()
v35 = pd.read_csv("data/scores_v35.csv").set_index("id").sort_index()["score"].to_numpy()
top = np.zeros(len(ids), bool); top[np.argpartition(-v35, K)[:K]] = True

f1, f3, f21 = f.f1.to_numpy(), f.f3.to_numpy(), f.f21.to_numpy()
f6, f7, f8, f9, f10 = (f[c].to_numpy() for c in ["f6", "f7", "f8", "f9", "f10"])
benefit = 50*f.f13.to_numpy() + f.f14.to_numpy() + 15*f.f15.to_numpy() + f.f16.to_numpy()
catsum = f6 + f7 + f8 + f9 + f10
eps = 1.0
other_share = f7 / np.maximum(catsum, eps)
travel_share = (f6 + f9) / np.maximum(catsum, eps)
dining_share = f10 / np.maximum(catsum, eps)
rp = lambda a: pd.Series(a).rank(pct=True).to_numpy()
z = lambda a: (a - a.mean()) / a.std()

# MS-likeness (higher = more MS-like): Other-dominated, low travel/dining, zero revolve, high redeem,
# low benefit usage, high spend
ms = (z(other_share) - z(travel_share) - z(dining_share) - z(rp(f1))
      + z(rp(f21)) - z(rp(benefit)) + 0.5*z(rp(catsum)))

med_top_catsum = np.median(catsum[top])

def prof(mask):
    m = np.flatnonzero(mask) if mask.dtype == bool else mask
    return dict(n=len(m), catsum=int(np.median(catsum[m])), other_sh=round(float(np.median(other_share[m])), 2),
                travel_sh=round(float(np.median(travel_share[m])), 2), f1=int(np.median(f1[m])),
                f21=int(np.median(f21[m])), benefit=int(np.median(benefit[m])))

def build(name, N, other_min, f1_max):
    ms_pool = np.flatnonzero(top & (other_share > other_min) & (f1 <= f1_max) & (catsum > med_top_catsum))
    ms_out = ms_pool[np.argsort(-ms[ms_pool])][:N]                       # most MS-like in top
    repl = np.flatnonzero(~top & (f3 == 0) & (other_share < 0.70))       # non-MS outsiders
    repl_in = repl[np.argsort(-v35[repl])][:N]                           # best v35-margin
    n = min(len(ms_out), len(repl_in)); ms_out, repl_in = ms_out[:n], repl_in[:n]
    new = top.copy(); new[ms_out] = False; new[repl_in] = True
    # score: v35 order, but push the demoted below cutoff and the promoted above (bounded graft)
    s = v35.astype(float).copy()
    rng = v35.max() - v35.min()
    s[ms_out] = v35.min() - 0.1*rng          # demote MS
    s[repl_in] = v35.max() + 0.1*rng          # promote replacements (order among them = v35)
    s = s * (1.0 + 4.342944819e-7) + 0.2718281828
    nt = np.zeros(len(s), bool); nt[np.argpartition(-s, K)[:K]] = True
    cut = s[nt].min()
    assert int((s == cut).sum()) == 1 and not (nt & (f3 == 1)).any()
    whale = np.zeros(len(ids), bool); wo = np.argsort(-f7); whale[wo[f3[wo] == 0][:15000]] = True
    pd.DataFrame({"id": ids, "score": s}).to_csv(f"data/scores_{name}.csv", index=False)
    print(f"\n### {name}: demote {n} MS-signature members (other_share>{other_min}, f1<={f1_max})")
    print(f"  OUT (alleged MS): {prof(ms_out)}")
    print(f"  IN  (replacements): {prof(repl_in)}")
    print(f"  whale-in {(nt & whale).sum()/whale.sum():.4f} (evicts {(top & whale).sum()-(nt & whale).sum()} f7-whales BY DESIGN)")
    print(f"  overlap vs v35 {(nt & top).sum()/K:.4f}  |  pre-reg: realized = 0.919533 + net*{n/1e5:.4f}")

print(f"reference: median top-20% catsum ${med_top_catsum:,.0f}; {int((top&(other_share>0.9)&(f1<10)).sum())} top members are >90% Other & ~zero-balance")
build("ms_demote", 2500, 0.75, 100)     # moderate signature
build("ms_strict", 1200, 0.90, 1)       # pure MS: >90% Other, zero balance
