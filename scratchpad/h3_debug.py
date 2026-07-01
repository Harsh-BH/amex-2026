import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from eda import PremierEDA, SPEND_CATS
from score_magnitude import dollar_profit_v19_lending, _allpos_score, RECOVERED_W_V19, RECOVERED_RISK_W, spend_dollars
from lb_predict import LBPredictor, TOP

df = PremierEDA().df
f = df.fillna(0.0)   # <-- this is the key difference: actual v19 uses df.fillna(0.0), NOT cat_sp's no-bd avg-mix fill
has_bd = df[SPEND_CATS].notna().any(axis=1).to_numpy()
real_v19 = dollar_profit_v19_lending(df).to_numpy()

# reconstruct using f.fillna(0) directly (NOT my avg-mix-split cat_sp)
score = np.zeros(len(df))
for k, wv in RECOVERED_W_V19.items():
    v = f[k].to_numpy()
    score += wv * v / (v.std() + 1e-9)
expl = -(f["f11"].to_numpy() * f["f1"].to_numpy())
score += RECOVERED_RISK_W * expl / (expl.std() + 1e-9)
f3 = (f["f3"].to_numpy() == 1)
score2 = score.copy(); score2[f3] = score2.min() - 1.0

N = len(df); TOPN = 100_000
def topmask(s):
    m = np.zeros(N, bool); m[np.argpartition(-s, TOPN)[:TOPN]] = True; return m
a, b = topmask(score2), topmask(real_v19)
print("Jaccard reconstruction(fillna0 directly) vs real v19:", (a&b).sum()/(a|b).sum())
print("max abs diff:", np.max(np.abs(score2 - real_v19)))

# my cat_sp version: where does the no-bd cohort's f6/f9 differ from fillna(0)?
print("\nfillna(0) f6 for no-bd (should be 0):", f["f6"].to_numpy()[~has_bd][:5])
print("no-bd count:", (~has_bd).sum())
