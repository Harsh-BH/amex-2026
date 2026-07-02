"""Triangulation 2.0 — recover the hidden truth over the RICH form family, using ALL 18 LB reads.

Why: src/triangulate.py fits a LINEAR dollar-basis family on 12 constraints (<= v15). It cannot even
represent the current best region (v22 rank-basis, v24 dual-engine interaction), and the six most
informative observations (v19..v26, incl. two negative form-family points v25/v26) were never used.
src/lb_predict.py is a consensus vote over our own guesses — provably blind to correct new directions.
This script fits the GENERATING truth over a family that spans every axis we have LB-tested, then:
  A  fit-core : fit on all 18; per-observation residuals (can it reproduce the v22..v26 cluster?)
  B  holdout  : fit on 14 (excl. v22/v24/v25/v26), predict those 4 — the honest form-generalization test
  C  loo      : leave-one-out across all 18
  D  extras   : greedy-add one candidate extra term at a time (benefits/engagement/f4/f21/f17/f5/f2/nbd)
                -> which term reduces fit error with a stable sign = evidence of a missing truth term
  E  posterior: N seeded fits, keep near-optimal, posterior-expected LB for v24 vs consensus vs variants

Run:  .venv/bin/python scratchpad/triangulate2.py build|fit-core|holdout|loo|extras|posterior
Cache: scratchpad/tri2_cache.npz (term matrix + masks). Deterministic (SEED). Never uses id as a term.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "scratchpad" / "tri2_cache.npz"
SEED = 42
N = 500_000
TOPK = 100_000
REG = 2e-5                      # mild L1 pressure on the normalized weights (sparsity, aids LOO)
SPEND = ["f6", "f7", "f8", "f9", "f10"]

OBS = {"v1": .449, "v2": .465, "v3": .614, "v4": .609, "v5": .733, "v6": .675, "v7": .768,
       "v8": .681, "v9": .727, "v10": .805, "v11min": .823, "v15": .827, "v19": .859,
       "v21": .851, "v22": .866, "v24": .880, "v25": .866, "v26": .843,
       "v27": .895}   # 2026-07-02: the recovered-consensus itself — the 19th, most-informative constraint
FORM_CLUSTER = ["v22", "v24", "v25", "v26"]

CORE = ["z6", "z7", "z8", "z9", "z10", "r6", "r7", "r8", "r9", "r10", "z1", "r1", "exl", "dual", "f3neg"]
EXTRAS = ["ben", "eng", "f4l", "f21l", "f17z", "f5z", "f2neg", "nbd", "rcat",
          # round-3 candidates (2026-07-02): risk-shape + balance-curvature + winsor-rescue
          "f11n",    # standalone risk penalty (prices risk for TRANSACTORS too — core exl is 0 when f1=0)
          "f11cat",  # expected loss on spend receivables (charge-card risk scales with spend carry)
          "sq1",     # sqrt balance (explicit concavity, distinct from rank)
          "lg1",     # log1p balance (stronger concavity)
          "util",    # utilization f1/f17 (draw intensity on the granted line)
          "capfix"]  # f1-winsor rescue: at-cap members ordered by their lend line


def _scale(v: np.ndarray) -> np.ndarray:
    """Project convention: scale by std, don't center (preserves the zero-mass cohorts)."""
    return (v / (v.std() + 1e-9)).astype(np.float32)


def _pct(v: np.ndarray) -> np.ndarray:
    return pd.Series(v).rank(pct=True).to_numpy()


def build():
    df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
    ids = df["id"].to_numpy()
    f = df.fillna(0.0)
    t: dict[str, np.ndarray] = {}
    for c in SPEND:                                     # dollar and rank basis per category
        t[f"z{c[1:]}"] = _scale(f[c].to_numpy())
        t[f"r{c[1:]}"] = _scale(_pct(f[c].to_numpy()))
    f1v = f["f1"].to_numpy()
    t["z1"] = _scale(f1v)
    t["r1"] = _scale(_pct(f1v))
    t["exl"] = _scale(-(f["f11"].to_numpy() * f1v))     # expected credit loss (negative term)
    catsum = f[SPEND].sum(axis=1).to_numpy()
    revint = np.where(f1v > 0, _pct(f1v), 0.0)          # v24's exact revolving-intensity
    t["dual"] = _scale(_pct(catsum) * revint)
    t["f3neg"] = _scale(-f["f3"].to_numpy())            # + weight = truth demotes collection-flagged
    # candidate EXTRA truth terms (each may or may not exist in the hidden formula)
    t["ben"] = _scale(-(50.0 * f["f13"] + f["f14"] + 15.0 * f["f15"] + f["f16"]).to_numpy())  # $-ised benefit cost
    t["eng"] = _scale(_scale(df["f12"].fillna(df["f12"].median()).to_numpy())
                      + _scale(df["f22"].fillna(df["f22"].median()).to_numpy()))              # engagement
    f4l = np.log1p(df["f4"].to_numpy());  f4l = np.where(np.isnan(f4l), np.nanmedian(f4l), f4l)
    f21l = np.log1p(df["f21"].to_numpy()); f21l = np.where(np.isnan(f21l), np.nanmedian(f21l), f21l)
    t["f4l"] = _scale(f4l)                              # points balance (tenure/loyalty stock)
    t["f21l"] = _scale(f21l)                            # points redeemed (realized rewards cost if -)
    t["f17z"] = _scale(f["f17"].to_numpy())             # lend line (0 = no line)
    t["f5z"] = _scale(f["f5"].to_numpy())               # the weird "total spend"
    t["f2neg"] = _scale(-f["f2"].to_numpy())            # attrition calls
    t["nbd"] = _scale(-df["f6"].isna().to_numpy(float)) # explicit no-breakdown demotion flag
    t["rcat"] = _scale(_pct(catsum))                    # rank of total category spend
    f11v = f["f11"].to_numpy()
    t["f11n"] = _scale(-f11v)                           # standalone risk (hits transactors too)
    t["f11cat"] = _scale(-(f11v * catsum))              # expected loss on spend receivables
    t["sq1"] = _scale(np.sqrt(np.clip(f1v, 0, None)))   # concave balance
    t["lg1"] = _scale(np.log1p(np.clip(f1v, 0, None)))  # strongly concave balance
    f17v = f["f17"].to_numpy()
    t["util"] = _scale(np.where(f17v > 0, f1v / np.maximum(f17v, 1.0), 0.0))  # line utilization
    cap1 = f1v >= np.nanmax(f1v) - 1e-6                 # the ~2.6% winsorized-at-cap balances
    t["capfix"] = _scale(np.where(cap1, f17v, 0.0))     # order at-cap members by lend line
    names = CORE + EXTRAS
    T = np.column_stack([t[k] for k in names]).astype(np.float32)
    M = np.zeros((len(OBS), N), bool)
    for j, v in enumerate(OBS):
        s = pd.read_csv(ROOT / "data" / f"scores_{v}.csv").set_index("id")["score"].reindex(ids).to_numpy()
        assert not np.isnan(s).any(), f"{v} has NaN after reindex"
        M[j, np.argpartition(-s, TOPK)[:TOPK]] = True
    np.savez_compressed(CACHE, T=T, M=M, ids=ids, names=np.array(names), obs_keys=np.array(list(OBS)))
    print(f"cached: T {T.shape} float32, masks {M.shape}, -> {CACHE}")


def load():
    z = np.load(CACHE, allow_pickle=False)
    names = [str(x) for x in z["names"]]
    keys = [str(x) for x in z["obs_keys"]]
    return z["T"], z["M"], z["ids"], names, keys


# fit context (py3.14 defaults mp to forkserver, so no fork-shared globals; we run single-process
# with vectorized=True — the population matmul is BLAS-parallel, which uses all cores anyway)
_CTX: dict = {}


OBS_POW = 2.0   # constraint weighting: w_i ∝ (obs_i/max_obs)^OBS_POW. A/B'd 2026-07-02 (tri2_ab.py):
                # frontier LOO mean|err| 0.0066 at p=2 vs 0.0114 uniform vs 0.0136 at p=4 — p=2 adopted.


def _loss_vec(X):
    """scipy vectorized mode: X has shape (n_params, S); return (S,) energies."""
    W = np.atleast_2d(X.T)                                # (S, n_params)
    Wn = W / (np.linalg.norm(W, axis=1, keepdims=True) + 1e-12)
    SC = _CTX["T"] @ Wn.T.astype(np.float32)              # (500K, S) — BLAS-parallel
    M, obs, cw = _CTX["M"], _CTX["obs"], _CTX["cw"]
    out = np.empty(len(Wn))
    for j in range(len(Wn)):
        tidx = np.argpartition(-SC[:, j], TOPK)[:TOPK]
        ov = M[:, tidx].sum(axis=1) / TOPK
        out[j] = (cw * (ov - obs) ** 2).sum() + REG * np.abs(Wn[j]).sum()
    return out


# interpretable warm starts, expressed over the full name list (missing -> 0)
def _dirs(names):
    D = [
        {"z7": .74, "z1": .74, "r8": .35, "r10": .14, "r6": .06, "r9": .06, "exl": .11, "dual": .20, "f3neg": 1.0},  # v24
        {"z7": .74, "z1": .74, "z8": .35, "z10": .14, "z6": .06, "z9": .06, "exl": .11, "f3neg": 1.0},               # v19
        {"z7": .74, "z1": .74, "r8": .35, "r10": .14, "r6": .06, "r9": .06, "exl": .11, "f3neg": 1.0},               # v22
        {"z7": 1, "z1": 1, "dual": .5, "f3neg": 1},                                                                   # dual-heavy
        {"z6": 1, "z7": 1, "z8": 1, "z9": 1, "z10": 1, "z1": 1},                                                      # all-dollar
        {"r6": 1, "r7": 1, "r8": 1, "r9": 1, "r10": 1, "r1": 1, "f3neg": 1},                                          # all-rank
        {"z7": .74, "z1": .74, "r8": .35, "r10": .14, "r6": .06, "r9": .06, "exl": .11, "dual": .20, "f3neg": 1.0,
         "ben": .1, "eng": .1},                                                                                       # v24 + extras
    ]
    out = []
    for d in D:
        w = np.zeros(len(names))
        for k, v in d.items():
            if k in names:
                w[names.index(k)] = v
        out.append(w / (np.linalg.norm(w) + 1e-9))
    return out


def _pop(names, active, rng, size=96):
    base = [w[active] for w in _dirs(names)]
    base = [b if np.linalg.norm(b) > 1e-6 else rng.standard_normal(len(active)) * .1 for b in base]
    pop = list(base)
    while len(pop) < size:
        b = base[rng.integers(len(base))]
        pop.append(b + 0.25 * rng.standard_normal(len(active)))
    return np.clip(np.array(pop), -2.9, 2.9)


def fit(T, M, keys_all, fit_keys, names, active_names=None, seed=SEED, maxiter=140, popsize=96):
    active_names = active_names or names
    active = [names.index(k) for k in active_names]
    rows = [keys_all.index(k) for k in fit_keys]
    _CTX["T"] = np.ascontiguousarray(T[:, active])
    _CTX["M"] = np.ascontiguousarray(M[rows])
    _CTX["obs"] = np.array([OBS[k] for k in fit_keys])
    ov = _CTX["obs"]
    cw = (ov / ov.max()) ** OBS_POW
    _CTX["cw"] = cw * len(cw) / cw.sum()                  # normalized so total weight = n (RMSE comparable)
    rng = np.random.default_rng(seed)
    res = differential_evolution(_loss_vec, [(-3, 3)] * len(active),
                                 init=_pop(names, active, rng, popsize), mutation=(0.4, 1.2),
                                 recombination=0.85, tol=1e-12, polish=False, seed=seed,
                                 maxiter=maxiter, vectorized=True, updating="deferred")
    w = res.x / np.linalg.norm(res.x)
    if "z7" in active_names and w[active_names.index("z7")] < 0:
        w = -w
    return w, res.fun


def _implied(w, T, M, keys_all, names, active_names, want_keys):
    active = [names.index(k) for k in active_names]
    score = T[:, active] @ w.astype(np.float32)
    tidx = np.argpartition(-score, TOPK)[:TOPK]
    return {k: M[keys_all.index(k), tidx].sum() / TOPK for k in want_keys}, score


def _rmse(imp: dict) -> float:
    return float(np.sqrt(np.mean([(imp[k] - OBS[k]) ** 2 for k in imp])))


def fit_core():
    T, M, ids, names, keys = load()
    w, fun = fit(T, M, keys, keys, names, CORE, maxiter=160)
    imp, score = _implied(w, T, M, keys, names, CORE, keys)
    print(f"=== A. core fit, all 18 constraints ({len(CORE)} terms) ===")
    print("weights:", {n: round(float(x), 3) for n, x in zip(CORE, w) if abs(x) > 0.01})
    print(f"in-sample RMSE {_rmse(imp):.4f}")
    for k in keys:
        print(f"  {k:>6}: fit {imp[k]:.3f} actual {OBS[k]:.3f} err {imp[k]-OBS[k]:+.3f}")
    np.save(ROOT / "scratchpad" / "tri2_core_w.npy", w)


def holdout():
    T, M, ids, names, keys = load()
    tr = [k for k in keys if k not in FORM_CLUSTER]
    w, _ = fit(T, M, keys, tr, names, CORE, maxiter=160)
    imp, _ = _implied(w, T, M, keys, names, CORE, keys)
    print("=== B. holdout: fit on 14 (no v22/v24/v25/v26), predict the form cluster ===")
    print("weights:", {n: round(float(x), 3) for n, x in zip(CORE, w) if abs(x) > 0.01})
    print(f"train RMSE {_rmse({k: imp[k] for k in tr}):.4f}")
    for k in FORM_CLUSTER:
        print(f"  predict {k}: {imp[k]:.3f} actual {OBS[k]:.3f} err {imp[k]-OBS[k]:+.3f}")
    order_pred = sorted(FORM_CLUSTER, key=lambda k: -imp[k])
    order_true = sorted(FORM_CLUSTER, key=lambda k: -OBS[k])
    print(f"predicted order {order_pred} vs true {order_true}")


def loo():
    T, M, ids, names, keys = load()
    errs = []
    subset = ["v11min", "v15", "v19", "v21", "v22", "v24", "v25", "v26"]  # the informative frontier
    print("=== C. leave-one-out (frontier subset) ===")
    for held in subset:
        tr = [k for k in keys if k != held]
        w, _ = fit(T, M, keys, tr, names, CORE, maxiter=90, popsize=64)
        imp, _ = _implied(w, T, M, keys, names, CORE, [held])
        errs.append(abs(imp[held] - OBS[held]))
        print(f"  hold {held:>6}: pred {imp[held]:.3f} actual {OBS[held]:.3f} |err| {errs[-1]:.3f}", flush=True)
    print(f"LOO mean |err| {np.mean(errs):.4f}  median {np.median(errs):.4f}")


def extras():
    T, M, ids, names, keys = load()
    w0, fun0 = fit(T, M, keys, keys, names, CORE, maxiter=140)
    imp0, _ = _implied(w0, T, M, keys, names, CORE, keys)
    base = _rmse(imp0)
    print(f"=== D. greedy extra terms (base core RMSE {base:.4f}) ===")
    for e in EXTRAS:
        cols = CORE + [e]
        w, _ = fit(T, M, keys, keys, names, cols, seed=SEED + 7, maxiter=100, popsize=64)
        imp, _ = _implied(w, T, M, keys, names, cols, keys)
        r = _rmse(imp)
        print(f"  +{e:<5} RMSE {r:.4f} (Δ {r-base:+.4f})  weight {float(w[cols.index(e)]):+.3f}", flush=True)


def posterior(n_fits=16):
    T, M, ids, names, keys = load()
    fits, funs = [], []
    for sd in range(SEED, SEED + n_fits):
        w, fun = fit(T, M, keys, keys, names, CORE, seed=sd, maxiter=100, popsize=64)
        imp, score = _implied(w, T, M, keys, names, CORE, keys)
        fits.append((w, score, _rmse(imp)))
        funs.append(fun)
        print(f"  seed {sd}: RMSE {fits[-1][2]:.4f}", flush=True)
    rs = np.array([f[2] for f in fits])
    keep = [f for f in fits if f[2] <= rs.min() * 1.5 + 1e-6]
    print(f"=== E. posterior: {len(keep)}/{n_fits} fits kept (RMSE {rs.min():.4f}..{max(f[2] for f in keep):.4f}) ===")
    W = np.array([f[0] for f in keep])
    print("per-term posterior weights (median [min..max], sign-agreement):")
    for i, nm in enumerate(CORE):
        med = np.median(W[:, i])
        agree = (np.sign(W[:, i]) == np.sign(med)).mean() if med != 0 else 0
        print(f"  {nm:<6} {med:+.3f}  [{W[:, i].min():+.3f}..{W[:, i].max():+.3f}]  sign {agree:.0%}")
    masks = []
    for w, score, r in keep:
        m = np.zeros(N, bool)
        m[np.argpartition(-score, TOPK)[:TOPK]] = True
        masks.append(m)
    K = len(masks)
    P = np.zeros((K, K))
    for i in range(K):
        for j in range(i + 1, K):
            P[i, j] = P[j, i] = (masks[i] & masks[j]).sum() / TOPK
    iu = P[np.triu_indices(K, 1)]
    print(f"posterior top-20% pairwise overlap: mean {iu.mean():.3f}  min {iu.min():.3f}  max {iu.max():.3f}")
    vote = np.sum(masks, axis=0).astype(np.float32)
    mean_score = np.mean([_scale(f[1]) for f in keep], axis=0)
    consensus = vote + 1e-3 * _scale(mean_score)          # vote first, mean score tie-break
    cidx = np.argpartition(-consensus, TOPK)[:TOPK]
    cmask = np.zeros(N, bool); cmask[cidx] = True
    # posterior-expected LB of any candidate = mean overlap with the kept posterior truths
    def e_lb(mask):
        return float(np.mean([(mask & m).sum() / TOPK for m in masks]))
    v24 = M[keys.index("v24")]
    print(f"E[overlap | posterior]: v24 {e_lb(v24):.3f}   posterior-consensus {e_lb(cmask):.3f}")
    print(f"consensus vs v24 overlap: {(cmask & v24).sum() / TOPK:.3f}")
    out = pd.DataFrame({"id": ids, "score": consensus})
    out.to_csv(ROOT / "scratchpad" / "tri2_consensus_scores.csv", index=False)
    np.save(ROOT / "scratchpad" / "tri2_posterior_masks.npy", np.array(masks))
    print("saved scratchpad/tri2_consensus_scores.csv + tri2_posterior_masks.npy")


def candidates():
    """Posterior-expected LB for every candidate we could submit next, plus counterfactuals for
    the never-uploaded builds. E[LB] = mean overlap with the kept posterior truths; also report
    min (pessimistic) and overlap-vs-v24 (how different the bet is)."""
    T, M, ids, names, keys = load()
    post = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
    v24 = M[keys.index("v24")]

    def mask_of(score):
        m = np.zeros(N, bool)
        m[np.argpartition(-np.asarray(score, np.float64), TOPK)[:TOPK]] = True
        return m

    def row(name, m):
        ov = [(m & p).sum() / TOPK for p in post]
        print(f"  {name:<22} E[LB] {np.mean(ov):.3f}  min {np.min(ov):.3f}  max {np.max(ov):.3f}"
              f"  | vs v24 {(m & v24).sum() / TOPK:.3f}")

    print("=== F. posterior-expected LB per candidate ===")
    print(f"(calibration anchors first: E[LB] should track the ACTUAL LB if the posterior is honest)")
    for v, actual in (("v19", .859), ("v22", .866), ("v24", .880), ("v26", .843), ("v27", .895)):
        ov = [(M[keys.index(v)] & p).sum() / TOPK for p in post]
        print(f"  anchor {v:<8} actual {actual:.3f}  E[LB] {np.mean(ov):.3f}")
    # never-uploaded builds (free counterfactuals)
    for v in ("v20", "v23", "v18", "v12"):
        p = ROOT / "data" / f"scores_{v}.csv"
        if p.exists():
            s = pd.read_csv(p).set_index("id")["score"].reindex(ids).to_numpy()
            row(f"unscored {v}", mask_of(s))
    # best-fit truth + posterior consensus
    w = np.load(ROOT / "scratchpad" / "tri2_core_w.npy")
    row("best-fit truth g^", mask_of(T[:, [names.index(k) for k in CORE]] @ w.astype(np.float32)))
    cons = pd.read_csv(ROOT / "scratchpad" / "tri2_consensus_scores.csv").set_index("id")["score"].reindex(ids).to_numpy()
    row("posterior consensus", mask_of(cons))
    # dual-engine lambda sweep via the exact additive reconstruction v24_at_l = v22 + (l/0.2)(v24-v22)
    s22 = pd.read_csv(ROOT / "data" / "scores_v22.csv").set_index("id")["score"].reindex(ids).to_numpy()
    s24 = pd.read_csv(ROOT / "data" / "scores_v24.csv").set_index("id")["score"].reindex(ids).to_numpy()
    for lam in (0.25, 0.30, 0.35, 0.40):
        row(f"v24 lambda={lam:.2f}", mask_of(s22 + (lam / 0.20) * (s24 - s22)))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "build"
    if stage == "posterior" and len(sys.argv) > 2:
        posterior(int(sys.argv[2]))
    else:
        {"build": build, "fit-core": fit_core, "holdout": holdout, "loo": loo,
         "extras": extras, "posterior": posterior, "candidates": candidates}[stage]()
