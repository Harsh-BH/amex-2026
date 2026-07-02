"""A/B the fit procedure by frontier leave-one-out: constraint weighting OBS_POW in {0, 2, 4}.
Higher OBS_POW makes the fit care more about reproducing the high-overlap (frontier) reads,
which is where the top-20% boundary information lives. Adopt whichever minimizes LOO error
on the frontier holdouts — a zero-submission-cost instrument upgrade.
Run: .venv/bin/python scratchpad/tri2_ab.py
"""
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triangulate2 as t2

HOLD = ["v19", "v21", "v22", "v24", "v26", "v27"]   # the frontier — where the next candidate lives

T, M, ids, names, keys = t2.load()
for p in (0.0, 2.0, 4.0):
    t2.OBS_POW = p
    errs = {}
    for held in HOLD:
        tr = [k for k in keys if k != held]
        w, _ = t2.fit(T, M, keys, tr, names, t2.CORE, maxiter=90, popsize=64)
        imp, _ = t2._implied(w, T, M, keys, names, t2.CORE, [held])
        errs[held] = imp[held] - t2.OBS[held]
    ae = np.abs(list(errs.values()))
    print(f"OBS_POW={p:g}: mean|err| {ae.mean():.4f}  max {ae.max():.4f}  "
          f"per-holdout {{{', '.join(f'{k}:{v:+.3f}' for k, v in errs.items())}}}", flush=True)
