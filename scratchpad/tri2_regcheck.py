"""REG sensitivity: refit the core family at REG=0 and REG x10; if the recovered structure
(z1 dominance, exl weight, rank-terms ~0) survives, it isn't a regularization artifact.
Run: .venv/bin/python scratchpad/tri2_regcheck.py
"""
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triangulate2 as t2

T, M, ids, names, keys = t2.load()
for reg in (0.0, 2e-4):
    t2.REG = reg
    w, _ = t2.fit(T, M, keys, keys, names, t2.CORE, seed=42, maxiter=110, popsize=64)
    imp, _ = t2._implied(w, T, M, keys, names, t2.CORE, keys)
    big = {n: round(float(x), 3) for n, x in zip(t2.CORE, w) if abs(x) > 0.05}
    print(f"REG={reg:g}: RMSE {t2._rmse(imp):.4f}  weights>|0.05|: {big}", flush=True)
