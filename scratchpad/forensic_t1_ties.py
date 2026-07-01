"""Forensic Thread 1: TIE STRUCTURE at the top-20% boundary.
v19 produces ~402K distinct scores -> ~98K ties. Are ties concentrated AT the cutoff (rank 90-110K)?
"""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA, SPEND_CATS
from score_magnitude import dollar_profit_v19_lending
from lb_predict import LBPredictor, TOP
import numpy as np
import pandas as pd

df = PremierEDA().df
ids = df["id"].to_numpy()
s19 = dollar_profit_v19_lending(df).to_numpy()
N = len(s19)

# --- basic tie census ---
vals, counts = np.unique(s19, return_counts=True)
n_distinct = len(vals)
n_tied_rows = counts[counts > 1].sum()
print(f"N={N}  distinct scores={n_distinct}  rows involved in >1-tie={n_tied_rows} ({n_tied_rows/N:.1%})")
print(f"max tie-group size={counts.max()}  groups with size>1: {(counts>1).sum()}")
print(f"tie-group size distribution (top 15 by size):")
order_c = np.argsort(-counts)[:15]
for i in order_c:
    print(f"  value={vals[i]:.6f}  count={counts[i]}")

# --- where does ties sit in rank space? ---
# argsort descending -> rank 0 = highest score. Use 'min' rank style (ties share lowest rank in group = stable join)
order = np.argsort(-s19, kind="stable")  # stable: ties broken by original index order (arbitrary, as v19 would do in a stable sort)
ranked_score = s19[order]

# For each row in order, find tie-group rank-span: use a value->(first_rank,last_rank) via searching sorted unique desc
sorted_desc_vals = vals[::-1]
sorted_desc_counts = counts[::-1]
cum = np.concatenate([[0], np.cumsum(sorted_desc_counts)])
# rank of group g spans [cum[g], cum[g+1])
# the cutoff at rank=TOP (100,000) falls inside which group?
cutoff_group = np.searchsorted(cum, TOP, side="right") - 1
print(f"\nCutoff rank={TOP}: falls in group idx={cutoff_group}, "
      f"value={sorted_desc_vals[cutoff_group]:.6f}, "
      f"group spans ranks [{cum[cutoff_group]}, {cum[cutoff_group+1]}), size={sorted_desc_counts[cutoff_group]}")

# how many members in TOTAL are tied with the cutoff group's value? (i.e., genuinely ambiguous in/out)
cutoff_val = sorted_desc_vals[cutoff_group]
n_tied_at_cutoff = (s19 == cutoff_val).sum()
n_in_from_group = cum[cutoff_group+1] - TOP  # how many of group must be excluded
n_out_from_group = TOP - cum[cutoff_group]   # how many of group are included
print(f"members tied AT exact cutoff value: {n_tied_at_cutoff}")
print(f"of these, {n_out_from_group} get included (arbitrary) and {n_in_from_group} excluded (arbitrary) by current sort")

# --- broader boundary band: how many distinct score values in rank 90k-110k? how many tie-groups straddle 100k? ---
band_lo, band_hi = 90_000, 110_000
band_scores = ranked_score[band_lo:band_hi]
band_vals, band_counts = np.unique(band_scores, return_counts=True)
print(f"\nBoundary band [{band_lo}:{band_hi}] (20,000 members): {len(band_vals)} distinct score values "
      f"({len(band_vals)/(band_hi-band_lo):.1%} distinct rate)  vs population overall distinct rate {n_distinct/N:.1%}")

# any single value spans > 1 member at the band? how many ties (>=2) in narrower bands around 100k
for lo, hi in [(95_000, 105_000), (98_000, 102_000), (99_000, 101_000), (99_500, 100_500)]:
    seg = ranked_score[lo:hi]
    u, c = np.unique(seg, return_counts=True)
    tie_frac = (c[c > 1].sum()) / len(seg) if len(seg) else float("nan")
    print(f"  band [{lo}:{hi}] ({hi-lo}): distinct={len(u)}  tie-rate={tie_frac:.1%}  max tie-size={c.max() if len(c) else 0}")

# population-wide: what is the SAME distinct-rate inside band vs outside?
full_u, full_c = np.unique(s19, return_counts=True)
overall_distinct_rate = len(full_u) / N
print(f"\noverall distinct rate = {overall_distinct_rate:.1%} (n_distinct={len(full_u)})")
# top tier vs bottom tier comparison
top_seg = ranked_score[:TOP]
bot_seg = ranked_score[TOP:]
ut, ct = np.unique(top_seg, return_counts=True)
ub, cb = np.unique(bot_seg, return_counts=True)
print(f"TOP-20% (rank<{TOP}): distinct={len(ut)}/{TOP} ({len(ut)/TOP:.1%})  tie-rows={(ct[ct>1]).sum()}")
print(f"BOTTOM-80%: distinct={len(ub)}/{len(bot_seg)} ({len(ub)/len(bot_seg):.1%})  tie-rows={(cb[cb>1]).sum()}")

