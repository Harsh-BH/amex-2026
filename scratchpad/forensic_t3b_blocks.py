"""Thread 3b: test if missingness blocks are INDEPENDENT (combinatorial) vs forming discrete clusters,
then check if the missingness signature predicts profitability (v19 score) beyond what's captured already."""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA, SPEND_CATS
from score_magnitude import dollar_profit_v19_lending
import numpy as np
import pandas as pd

df = PremierEDA().df
FEATS = [f"f{i}" for i in range(1, 24)]
miss = df[FEATS].isna()
s19 = dollar_profit_v19_lending(df).to_numpy()
order_rank = pd.Series(s19).rank(ascending=False, method="first").to_numpy()
N = len(df)
in_top20 = order_rank <= 100_000

# define the 6 candidate independent missingness BLOCKS (booleans, one per block)
blocks = {
    "B_catspend":  miss["f6"],                                # f6-f10 co-miss (verified identical)
    "B_rewards":   miss["f4"],                                # f4+f21 co-miss
    "B_lendline":  miss["f17"],                                # f17 (f18 mostly co-misses but not perfectly, test below)
    "B_lendline2": miss["f18"],
    "B_benefits":  miss["f13"],                                # f13-f16 co-miss
    "B_emailclick":miss["f23"],
    "B_emailopen": miss["f22"],
    "B_login":     miss["f12"],
}
print("=== A. verify co-miss blocks are EXACTLY identical (as claimed in feature-notes) ===")
print(f"  f6==f7==f8==f9==f10 missingness identical: {(miss['f6']==miss['f7']).all() and (miss['f7']==miss['f8']).all() and (miss['f8']==miss['f9']).all() and (miss['f9']==miss['f10']).all()}")
print(f"  f4==f21 missingness identical: {(miss['f4']==miss['f21']).all()}")
print(f"  f13==f14==f15==f16 missingness identical: {(miss['f13']==miss['f14']).all() and (miss['f14']==miss['f15']).all() and (miss['f15']==miss['f16']).all()}")
print(f"  f17==f18 missingness identical: {(miss['f17']==miss['f18']).all()}  (jaccard if not: )")
if not (miss['f17']==miss['f18']).all():
    inter = (miss['f17'] & miss['f18']).sum()
    union = (miss['f17'] | miss['f18']).sum()
    print(f"    f17-miss n={miss['f17'].sum()}  f18-miss n={miss['f18'].sum()}  intersection={inter}  union={union}  jaccard={inter/union:.3f}")
    print(f"    f17 missing & f18 present: {(miss['f17'] & ~miss['f18']).sum()}")
    print(f"    f18 missing & f17 present: {(miss['f18'] & ~miss['f17']).sum()}")

print("\n=== B. test BLOCK INDEPENDENCE: are catspend-miss, rewards-miss, lendline-miss independent flags? ===")
B = pd.DataFrame({
    "catspend_miss": miss["f6"],
    "rewards_miss": miss["f4"],
    "lendline_miss": miss["f17"],
    "benefits_miss": miss["f13"],
})
print(f"  marginal rates: {B.mean().to_dict()}")
print(f"  pairwise observed-vs-chance joint P(both missing):")
for i,a in enumerate(B.columns):
    for b in B.columns[i+1:]:
        obs = (B[a] & B[b]).mean()
        chance = B[a].mean() * B[b].mean()
        print(f"    {a} & {b}: observed={obs:.4f}  chance(indep)={chance:.4f}  ratio={obs/chance:.3f}")

print("\n=== C. signature -> profitability (v19 score) profile: does missingness ALONE predict v19 rank? ===")
sig = miss.apply(lambda r: tuple(r[["f4","f6","f17","f13","f22","f23"]].values), axis=1)
prof = pd.DataFrame({"sig": sig, "s19": s19, "in_top20": in_top20})
g = prof.groupby("sig").agg(n=("s19","size"), mean_s19=("s19","mean"), top20_rate=("in_top20","mean")).sort_values("n", ascending=False)
print(f"  reduced to {len(g)} signatures (using f4,f6,f17,f13,f22,f23 as block representatives)")
print(g.head(20).to_string())
print(f"\n  population top20 rate baseline = {in_top20.mean():.2%}")
