"""Can we reproduce the banked data/scores_v35.csv from the FROZEN vintage inputs?
build_v35.py's live inputs were overwritten 07-04 (masks K=30->12). scratchpad/v35_frozen/ holds
the K=30 masks + fit6 weights from 07-03. T/ids/names are deterministic from premier.pkl. If this
reproduces scores_v35.csv byte-for-byte, the DQ reproducibility risk closes by repointing the build.
Run: .venv/bin/python scratchpad/repro_v35.py"""
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK, N_MAX, GAP_FLOOR = 100_000, 2_000, 0.40
V34_EXACT = 0.917614
SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)   # T/ids/names deterministic
T, ids = z["T"], z["ids"]
names = [str(x) for x in z["names"]]
post = np.load(ROOT / "scratchpad" / "v35_frozen" / "tri2_posterior_masks.npy")   # FROZEN K=30
w6 = np.load(ROOT / "scratchpad" / "v35_frozen" / "tri2_fit6_w.npy")               # FROZEN
print(f"frozen posterior K = {post.shape[0]} (v35 needs 30)")

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all()
f3 = df["f3"].fillna(0).to_numpy()
s34 = pd.read_csv(ROOT / "data" / "scores_v34.csv").set_index("id")["score"].reindex(ids).to_numpy()
m34 = np.zeros(len(s34), bool); m34[np.argpartition(-s34, TOPK)[:TOPK]] = True

vote = post.sum(axis=0).astype(np.float64)
margin = (T[:, [names.index(k) for k in SIX]].astype(np.float64)) @ w6
tb = margin / margin.std()
base_new = vote + 1e-3 * tb

in_pool = np.flatnonzero(~m34 & (f3 == 0)); out_pool = np.flatnonzero(m34)
in_pool = in_pool[np.lexsort((-tb[in_pool], -vote[in_pool]))]
out_pool = out_pool[np.lexsort((tb[out_pool], vote[out_pool]))]
gaps = (vote[in_pool[:6000]] - vote[out_pool[:6000]]) / TOPK
n_apply = int(min(N_MAX, np.searchsorted(-gaps, -GAP_FLOOR)))
target = m34.copy(); target[out_pool[:n_apply]] = False; target[in_pool[:n_apply]] = True

BIG = 2.0 * (base_new.max() - base_new.min())
score = base_new + BIG * target
score[f3 == 1] = score.min() - 1.0
score = score + 0.2718281828

v35 = pd.read_csv(ROOT / "data" / "scores_v35.csv").set_index("id")["score"].reindex(ids).to_numpy()
maxdiff = np.abs(score - v35).max()
top_repro = np.zeros(len(score), bool); top_repro[np.argpartition(-score, TOPK)[:TOPK]] = True
top_v35 = np.zeros(len(v35), bool); top_v35[np.argpartition(-v35, TOPK)[:TOPK]] = True
print(f"chosen N = {n_apply}")
print(f"max |score_repro - score_v35| = {maxdiff:.2e}")
print(f"top-20% set identical: {(top_repro == top_v35).all()}  (symmetric diff {int((top_repro ^ top_v35).sum())})")
print("VERDICT:", "BYTE-REPRODUCIBLE ✓ (fix = repoint build to v35_frozen)" if maxdiff < 1e-9
      else "NOT byte-identical, but ranking may match" if (top_repro == top_v35).all()
      else "REPRODUCTION FAILED — deeper problem")
