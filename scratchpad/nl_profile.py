"""Profile the concave-spend divergence from v15: WHO moves, are mega-spenders demoted (the v15-win
risk), and does an intermediate concavity sit between sqrt and log. Also probe whether a STRONGER
segment differentiation (revolvers get risk-scaled, transactors pure-spend) diverges more than the
near-identical v16_segment. No submission; no label."""
import numpy as np, pandas as pd
import sys; sys.path.insert(0, "src")
from eda import PremierEDA, SPEND_CATS
import score_magnitude as sm

TOP = 100_000
df = PremierEDA().df
f = df.fillna(0.0)
catsum = df[SPEND_CATS].sum(axis=1, min_count=1).fillna(0.0).to_numpy()
is_rev = (f.f1.values > 0)

def top(s): return set(pd.Series(np.asarray(s)).nlargest(TOP).index)
def jac(a, b): A, B = top(a), top(b); return len(A & B) / len(A | B)

s15 = sm.dollar_profit_v15_allpos(df).to_numpy()
t15 = top(s15)

# ---- concave family: who does mild-sqrt move vs v15, and where do mega-spenders go? ----
ssq = sm.dollar_profit_v16_sqrt(df).to_numpy()
r15 = pd.Series(-s15).rank(); rsq = pd.Series(-ssq).rank()
out = ((r15 <= TOP) & (rsq > TOP)).to_numpy()   # in v15 top, OUT of sqrt top
inn = ((r15 > TOP) & (rsq <= TOP)).to_numpy()
print("=== v16_sqrt (mild concave) vs v15: who moves ===")
print(f"  demoted {out.sum():,} | promoted {inn.sum():,}")
print(f"  DEMOTED  median catsum {pd.Series(catsum)[out].median():>8.0f}  f1 {df.loc[out,'f1'].fillna(0).median():>7.0f}  travelshare {((f.f6.values+f.f9.values)/(catsum+1))[out].mean():.3f}")
print(f"  PROMOTED median catsum {pd.Series(catsum)[inn].median():>8.0f}  f1 {df.loc[inn,'f1'].fillna(0).median():>7.0f}  travelshare {((f.f6.values+f.f9.values)/(catsum+1))[inn].mean():.3f}")
# are the very top mega-spenders (catsum>150k) still in?
mega = catsum > 150_000
print(f"  mega-spenders (catsum>150k, n={mega.sum()}): in v15 top {sum(mega[i] for i in t15)}  in sqrt top {sum(mega[i] for i in top(ssq))}")

# ---- intermediate concavity: x**0.75 sits between sqrt(0.5) and log ----
def powscore(p):
    score = np.zeros(len(df))
    for k, wv in sm.SPEND_W.items():
        score += wv * sm._z(np.clip(f[k].values, 0.0, None) ** p)
    score += sm.F1_W * sm._z(f.f1.values) + sm._expl_term(f)
    s = pd.Series(score, index=df.index)
    return s.mask(pd.Series(f.f3.values == 1, index=df.index), s.min() - 1.0).to_numpy()
for p in (0.85, 0.75, 0.65, 0.5):
    sp = powscore(p)
    print(f"  power p={p}: Jaccard~v15 {jac(sp, s15):.3f}  moved {len(top(sp) ^ t15)//2:,}  mega in {sum(mega[i] for i in top(sp))}")

# ---- stronger segment form: transactors pure-spend, revolvers spend x risk-quality + interest ----
# (more aggressive than v16_segment, which only ADDS lending margin to revolvers)
spend_rev = np.zeros(len(df))
for k, wv in sm.SPEND_W.items():
    spend_rev += wv * sm._z(np.clip(f[k].values, 0.0, None))
quality = 1.0 - sm.LGD * f.f11.values
interest = sm.F1_W * sm._z(f.f1.values)
# revolvers: (spend + interest) gated by quality ; transactors: spend only (no risk, no lending)
seg_strong = np.where(is_rev, (spend_rev + interest) * quality, spend_rev)
seg_strong = pd.Series(seg_strong, index=df.index)
seg_strong = seg_strong.mask(pd.Series(f.f3.values == 1, index=df.index), seg_strong.min()-1.0).to_numpy()
print(f"\n=== stronger segment (revolver=(spend+int)xquality, transactor=spend) ===")
print(f"  Jaccard~v15 {jac(seg_strong, s15):.3f}  moved {len(top(seg_strong) ^ t15)//2:,}  revolver share {sum(is_rev[i] for i in top(seg_strong))/TOP:.1%}")
