"""Does ANY non-linear shape on f1-f23 produce a LARGE, theory-coherent divergence from v15 in a
direction the LB might support (reward magnitude HARDER, or complementarity)? Probes convex spend,
a real spend x f1 interaction, and non-compensatory geometric aggregation. No submission; no label."""
import numpy as np, pandas as pd
import sys; sys.path.insert(0, "src")
from eda import PremierEDA, SPEND_CATS
import score_magnitude as sm

TOP = 100_000
df = PremierEDA().df
f = df.fillna(0.0)
catsum = df[SPEND_CATS].sum(axis=1, min_count=1).fillna(0.0).to_numpy()
is_rev = (f.f1.values > 0)
f3mask = pd.Series(f.f3.values == 1, index=df.index)

def top(s): return set(pd.Series(np.asarray(s)).nlargest(TOP).index)
def jac(a, b): A, B = top(a), top(b); return len(A & B) / len(A | B)
def screen(score):
    s = pd.Series(score, index=df.index); return s.mask(f3mask, s.min()-1.0).to_numpy()

s15 = sm.dollar_profit_v15_allpos(df).to_numpy(); t15 = top(s15)
mega = catsum > 150_000

# (1) CONVEX spend: x**1.5 — reward whales EVEN harder than linear (LB rewards magnitude)
def convex(p):
    sc = np.zeros(len(df))
    for k, wv in sm.SPEND_W.items():
        sc += wv * sm._z(np.clip(f[k].values, 0.0, None) ** p)
    sc += sm.F1_W * sm._z(f.f1.values) + sm._expl_term(f)
    return screen(sc)
for p in (1.25, 1.5, 2.0):
    sp = convex(p)
    print(f"convex p={p}: Jaccard~v15 {jac(sp,s15):.3f}  moved {len(top(sp)^t15)//2:,}  mega in {sum(mega[i] for i in top(sp))}/{mega.sum()}")

# (2) spend x f1 INTERACTION: best customers spend AND revolve. Add a complementarity bonus.
spend_rev = np.zeros(len(df))
for k, wv in sm.SPEND_W.items():
    spend_rev += wv * sm._z(np.clip(f[k].values, 0.0, None))
for gamma in (0.25, 0.5, 1.0):
    inter = gamma * sm._z(np.sqrt(np.clip(spend_rev - spend_rev.min(), 0, None)) * sm._z(f.f1.values))
    sc = spend_rev + sm.F1_W * sm._z(f.f1.values) + sm._expl_term(f) + inter
    si = screen(sc)
    print(f"spend*f1 inter gamma={gamma}: Jaccard~v15 {jac(si,s15):.3f}  moved {len(top(si)^t15)//2:,}  revolver share {sum(is_rev[i] for i in top(si))/TOP:.1%}")

# (3) NON-COMPENSATORY geometric mean across categories (must be broad, not one-category)
# weighted geometric mean of (1 + category $) — a one-category spender scores lower than a balanced one
logsum = np.zeros(len(df)); wsum = sum(sm.SPEND_W.values())
for k, wv in sm.SPEND_W.items():
    logsum += wv * np.log1p(np.clip(f[k].values, 0.0, None))
geo = np.expm1(logsum / wsum)   # weighted geometric mean dollars
sc = sm._z(geo) * sum(sm.SPEND_W.values()) + sm.F1_W * sm._z(f.f1.values) + sm._expl_term(f)
sg = screen(sc)
print(f"geometric (non-compensatory): Jaccard~v15 {jac(sg,s15):.3f}  moved {len(top(sg)^t15)//2:,}  mega in {sum(mega[i] for i in top(sg))}/{mega.sum()}")

# reference: how different are our OTHER real submissions from v15? (calibrates "meaningful divergence")
for v in ("v7", "v10", "v11min"):
    sv = pd.read_csv(f"data/scores_{v}.csv").sort_values("id")["score"].to_numpy()
    print(f"  REF scores_{v} vs v15: Jaccard {jac(sv, s15):.3f}")
