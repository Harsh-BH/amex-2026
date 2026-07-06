"""Structural audit: hunt a SHARED-preprocessing bug or a missed signal invisible to cross-version
checks. (1) missingness per feature; (2) never-modeled f12/f22/f23 — structured & orthogonal =
candidate missed signal; (3) no-breakdown-with-real-spend cohort = potential systematic false-neg;
(4) f7-refund handling. Read-only. Run: .venv/bin/python scratchpad/audit_structure.py"""
import numpy as np, pandas as pd

df = pd.read_pickle("data/premier.pkl").set_index("id").sort_index()
v35 = pd.read_csv("data/scores_v35.csv").set_index("id").sort_index()["score"]
K = 100_000
v35_rank = v35.rank(ascending=False, method="first")
in_top = v35_rank <= K
feats = [f"f{i}" for i in range(1, 24)]
MODELED = {"f1", "f3", "f6", "f7", "f8", "f9", "f10", "f11"}   # v35 core (+ probes touched most others)

print("=== (1) MISSINGNESS per feature (fillna(0) risk if missing != 0) ===")
for c in feats:
    miss = df[c].isna().mean()
    if miss > 0.001:
        print(f"  {c:4} miss {miss:6.1%}  nonmiss range [{df[c].min():.3g}, {df[c].max():.3g}]  median {df[c].median():.3g}")

print("\n=== (2) NEVER-MODELED f12/f22/f23: structured? orthogonal to modeled? ===")
fz = df.fillna(0.0)
proxies = {"f1_bal": fz.f1, "catsum": fz[["f6","f7","f8","f9","f10"]].sum(1), "f11_risk": fz.f11,
           "f4_pts": fz.f4, "f17_line": fz.f17, "f21_redeem": fz.f21}
for c in ["f12", "f22", "f23"]:
    s = df[c]
    print(f"  {c}: miss {s.isna().mean():.1%}  distinct {s.nunique()}  range [{s.min():.4g},{s.max():.4g}]  median {s.median():.4g}")
    sp_v35 = fz[c].corr(v35, method="spearman")
    best = max(proxies.items(), key=lambda kv: abs(fz[c].corr(kv[1], method="spearman")))
    print(f"       Spearman vs v35 score {sp_v35:+.3f}  |  max |corr| vs modeled = {best[0]} {fz[c].corr(best[1],method='spearman'):+.3f}")
    # is high-c a top-20% predictor beyond v35? in-top rate by c-quartile
    q = pd.qcut(fz[c].rank(method="first"), 4, labels=["Q1","Q2","Q3","Q4"])
    print(f"       in-top-20% rate by {c} quartile: " + "  ".join(f"{k} {in_top.groupby(q,observed=True).mean()[k]:.1%}" for k in ["Q1","Q2","Q3","Q4"]))

print("\n=== (3) NO-BREAKDOWN-WITH-SPEND cohort (catsum~0 but f5>0) — systematic false-neg? ===")
catsum = fz[["f6","f7","f8","f9","f10"]].sum(1)
nb = catsum.abs() < 1e-9
nb_spend = nb & (fz.f5 > 0)
print(f"  no-breakdown (catsum=0): {nb.sum():,} ({nb.mean():.1%})   of which f5>0: {nb_spend.sum():,}")
if nb_spend.sum():
    print(f"  their f5 median ${fz.loc[nb_spend,'f5'].median():,.0f} / max ${fz.loc[nb_spend,'f5'].max():,.0f}   f1(bal) median ${fz.loc[nb_spend,'f1'].median():,.0f}")
    print(f"  their v35 rank median {v35_rank[nb_spend].median():,.0f} / in-top-20%: {in_top[nb_spend].mean():.2%}  (are we burying real spenders?)")

print("\n=== (4) f7 REFUNDS (negative spend) ===")
neg = df.f7 < 0
print(f"  f7<0: {neg.sum():,} ({neg.mean():.1%})  median f7 when neg ${df.loc[neg,'f7'].median():,.0f}")
print(f"  their catsum median ${catsum[neg].median():,.0f}  v35 in-top-20%: {in_top[neg].mean():.2%}")
