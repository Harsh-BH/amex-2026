"""Provenance guard: refuse builds when posterior ensemble artifacts lag the constraint cache.

Run before ANY build_v*.py. Catches the refit26/refit27 failure mode where the 48-seed
posterior loop was interrupted and tri2_posterior_masks.npy silently stayed at an older
constraint vintage than tri2_cache.npz / tri2_core_w.npy.
"""
import sys
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parent
cache = R / "tri2_cache.npz"
n_obs = len(np.load(cache, allow_pickle=False)["obs_keys"])
print(f"cache: {n_obs} constraints, mtime {cache.stat().st_mtime:.0f}")
stale = [p.name for p in (R / "tri2_posterior_masks.npy", R / "tri2_consensus_scores.csv")
         if p.stat().st_mtime < cache.stat().st_mtime]
if stale:
    sys.exit(f"STALE ensemble artifacts (older than the cache): {stale}\n"
             f"-> rerun `.venv/bin/python scratchpad/triangulate2.py posterior 48` to completion first.")
print("OK: posterior artifacts are fresher than the cache.")
