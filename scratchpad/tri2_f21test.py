"""Does adding log-f21 fix the six strained constraints WITHOUT hurting frontier LOO?
Protocol: CORE vs CORE+f21l, at OBS_POW 0 (old constraints count) and 2 (frontier),
reporting per-strained-constraint residuals + frontier LOO. Zero submission cost."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import triangulate2 as t2

T, M, ids, names, keys = t2.load()
STRAIN = ["v1","v2","v3","v4","v6","v8"]
HOLD = ["v22","v24","v27","v29","v30"]

for fam_name, fam in (("CORE", t2.CORE), ("CORE+f21l", t2.CORE + ["f21l"])):
    for p in (0.0, 2.0):
        t2.OBS_POW = p
        w, _ = t2.fit(T, M, keys, keys, names, fam, maxiter=140, popsize=80)
        imp, _ = t2._implied(w, T, M, keys, names, fam, keys)
        sres = np.mean([abs(imp[k]-t2.OBS[k]) for k in STRAIN])
        fres = np.mean([abs(imp[k]-t2.OBS[k]) for k in HOLD])
        w21 = w[fam.index("f21l")] if "f21l" in fam else float("nan")
        print(f"{fam_name:<10} p={p:g}: strain-resid {sres:.4f}  frontier-resid {fres:.4f}  w(f21l) {w21:+.3f}", flush=True)

# frontier LOO with the term, at p=2 (the decisive test)
t2.OBS_POW = 2.0
errs = []
for held in HOLD:
    tr = [k for k in keys if k != held]
    w, _ = t2.fit(T, M, keys, tr, names, t2.CORE + ["f21l"], maxiter=110, popsize=72)
    imp, _ = t2._implied(w, T, M, keys, names, t2.CORE + ["f21l"], [held])
    errs.append(abs(imp[held]-t2.OBS[held]))
    print(f"  LOO hold {held}: |err| {errs[-1]:.4f}", flush=True)
print(f"CORE+f21l frontier LOO mean {np.mean(errs):.4f}  (CORE baseline ~0.0066)")
