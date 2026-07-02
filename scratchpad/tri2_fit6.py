"""Restricted refit: the interpretable 6-term P&L family {z1, z7, z9, z10, exl, f3neg}.
If this family alone reproduces the 18 observations nearly as well as the 15-term fit,
it becomes the submission candidate (fewer params = less overfit + clean Framework writeup).
Run: .venv/bin/python scratchpad/tri2_fit6.py
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from triangulate2 import load, fit, _implied, _rmse, OBS, ROOT, TOPK

SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]

T, M, ids, names, keys = load()
best = None
for sd in (42, 49, 77):
    w, _ = fit(T, M, keys, keys, names, SIX, seed=sd, maxiter=120, popsize=48)
    imp, score = _implied(w, T, M, keys, names, SIX, keys)
    r = _rmse(imp)
    print(f"seed {sd}: RMSE {r:.4f}  weights {dict(zip(SIX, np.round(w, 3)))}", flush=True)
    if best is None or r < best[0]:
        best = (r, w, imp, score)

r, w, imp, score = best
print(f"\nBEST 6-term fit RMSE {r:.4f} (15-term reference: 0.0027)")
for k in keys:
    print(f"  {k:>6}: fit {imp[k]:.3f} actual {OBS[k]:.3f} err {imp[k]-OBS[k]:+.3f}")
pd.DataFrame({"id": ids, "score": score}).to_csv(ROOT / "scratchpad" / "tri2_fit6_scores.csv", index=False)
np.save(ROOT / "scratchpad" / "tri2_fit6_w.npy", w)
print("saved scratchpad/tri2_fit6_scores.csv")
