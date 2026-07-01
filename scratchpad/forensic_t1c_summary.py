"""Thread 1 final: precise distance of giant tie groups from the cutoff (rank space)."""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA
from score_magnitude import dollar_profit_v19_lending
from lb_predict import TOP
import numpy as np
df = PremierEDA().df
s19 = dollar_profit_v19_lending(df).to_numpy()
order = np.argsort(-s19, kind="stable")
ranked = s19[order]
g1_val, g2_val = -1.005481, 0.0
g1_ranks = np.where(np.isclose(ranked, g1_val))[0]
g2_ranks = np.where(np.isclose(ranked, g2_val))[0]
print(f"f3-evict-floor group (-1.0055, n=54304): rank range [{g1_ranks.min()}, {g1_ranks.max()}] "
      f"= {g1_ranks.min()/len(s19):.0%}-{g1_ranks.max()/len(s19):.0%} percentile (bottom of population)")
print(f"no-breakdown-zero group (0.0, n=41779): rank range [{g2_ranks.min()}, {g2_ranks.max()}] "
      f"= {g2_ranks.min()/len(s19):.0%}-{g2_ranks.max()/len(s19):.0%} percentile")
print(f"cutoff is rank {TOP} ({TOP/len(s19):.0%}) -> nearest giant tie group is "
      f"{min(abs(g1_ranks.min()-TOP), abs(g2_ranks.max()-TOP))} ranks away")
print(f"\nmax tie-group size WITHIN top-20% (excluding any group entirely below the cutoff):")
top_vals, top_counts = np.unique(ranked[:TOP], return_counts=True)
print(f"  top-20% max tie size = {top_counts.max()}, at value {top_vals[np.argmax(top_counts)]:.4f}")
big = top_counts[top_counts>1]
print(f"  top-20% has {len(big)} tie-groups (size>1), total tied rows={big.sum()} ({big.sum()/TOP:.2%} of top-20%)")
