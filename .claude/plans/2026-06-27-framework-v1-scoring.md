# Framework v1 Scoring — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the v1 profitability score `(Revenue − Cost) × (1 − Risk)` over all 500K Premier cardmembers and prove its top-20% is stable — without spending a leaderboard submission.

**Architecture:** Two new modules in `src/`, both reusing the existing `PremierEDA` loader and raw `f1`–`f23` columns. `score.py` builds rank-normalized revenue/cost terms, applies per-segment business-prior weights, and writes a deterministic `id,score` file. `validation.py` measures top-20% membership stability under subsampling and weight perturbation (the label-free stand-in for the real metric). No submission file is produced — that's a later roadmap stage.

**Tech Stack:** Python 3.14 via `.venv/bin/python`, pandas 3.0.3, numpy 2.5.0. Test convention = `assert`-based `__main__` self-checks (project standard, NOT pytest).

## Global Constraints

(Copied from CLAUDE.md §16 + spec `.claude/memory/framework-design.md`. Every task implicitly includes these.)

- **Never use `id`** (or any identifier) as a predictor.
- **Use only existing variables `f1`–`f23`.** No external data.
- **Score every one of the 500K rows. No nulls in the score column.**
- **Rank-normalize every term to [0,1] before combining** (scales span ~6 orders of magnitude).
- **Missingness is a signal:** a missing input means that revenue/cost doesn't exist for the member → the term contributes **0**. Never fill-0 as a raw value.
- **Reproducible:** `SEED` is a named constant; deterministic; read columns by name; sort by `id` before writing.
- **No leaderboard submission in this plan.** The deliverable is a scored file + a passing stability report.
- **Commits only when the user asks** (CLAUDE.md §13) — no automatic commits in these tasks.

---

### Task 1: `src/score.py` — the scoring engine

**Files:**
- Create: `src/score.py`
- Reads: `docs/...data.xlsx` via `PremierEDA` (pickle-cached)
- Writes: `data/scores_v1.csv` (git-ignored)

**Interfaces:**
- Consumes: `from eda import PremierEDA, SPEND_CATS` (existing).
- Produces (later tasks rely on these exact names/signatures):
  - `segment(df: pd.DataFrame) -> pd.Series` → values in `{"transactor","revolver","lender"}`
  - `score(df: pd.DataFrame, weights: dict = WEIGHTS) -> pd.Series` → float score per row, no NaNs
  - `WEIGHTS: dict[str, tuple[float,float,float]]`, `SEGMENTS`, `SEED`

- [ ] **Step 1: Create `src/score.py` with constants + self-check + `main`, functions not yet defined**

```python
"""Premier-card profitability score — framework v1.

score = (Revenue − Cost) × (1 − Risk), all term inputs rank-normalized to [0,1],
one equation for all 500K with weights keyed by segment (transactor/revolver/lender).
Spec: .claude/memory/framework-design.md. Uses only f1–f23 (never id).

Run:  .venv/bin/python src/score.py     # self-checks, then scores 500K -> data/scores_v1.csv
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from eda import PremierEDA, SPEND_CATS

SEED = 42
OUT = Path(__file__).resolve().parent.parent / "data" / "scores_v1.csv"

# --- per-segment weights (v1 business priors; calibration = roadmap stage 6) ---
# value = (transactor, revolver, lender). Tilt to where each segment earns.
WEIGHTS = {
    "spending":       (1.00, 0.70, 0.70),   # interchange ≈ spend volume
    "balance_int":    (0.00, 0.80, 0.40),   # carried-balance interest
    "borrow_int":     (0.00, 0.00, 0.80),   # lending-line interest
    "depth":          (0.20, 0.20, 0.20),   # extra cards / supp fees
    "rewards_cost":   (0.50, 0.40, 0.40),   # redeemed + discounted liability
    "perks_cost":     (0.30, 0.30, 0.30),   # lounge/airline/cab/ent credits
    "servicing_cost": (0.15, 0.15, 0.15),   # cancel calls
}
SEGMENTS = ("transactor", "revolver", "lender")
REV_TERMS = ("spending", "balance_int", "borrow_int", "depth")
COST_TERMS = ("rewards_cost", "perks_cost", "servicing_cost")
RISK_A, RISK_B, RISK_CAP = 0.8, 0.2, 0.9   # risk = clamp(a*rank(f11) + b*f3, 0, cap)
REWARDS_LAMBDA = 0.5                        # weight of f4 contingent-liability vs realized f21


def main():
    _self_check()
    np.random.seed(SEED)
    df = PremierEDA().df
    s = score(df)
    assert s.notna().all(), "scored output has NaNs"
    out = pd.DataFrame({"id": df["id"], "score": s}).sort_values("id")
    OUT.parent.mkdir(exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"scored {len(out):,} rows -> {OUT}")
    print(out.score.describe().round(4))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it — verify it fails because the functions don't exist yet**

Run: `.venv/bin/python src/score.py`
Expected: FAIL — `NameError: name '_self_check' is not defined`

- [ ] **Step 3: Implement the term builders, segment tag, and combiner (insert above `main`)**

```python
def segment(df: pd.DataFrame) -> pd.Series:
    """transactor (charge-only, no balance) / revolver (balance, no lend line) / lender (has lend line)."""
    seg = pd.Series("transactor", index=df.index)
    seg[(df.f1 > 0) & df.f17.isna()] = "revolver"
    seg[df.f17.notna()] = "lender"           # lender rule wins
    return seg


def _rank(s: pd.Series) -> pd.Series:
    return s.rank(pct=True)                    # percentile in [0,1]; NaNs stay NaN


def spend_volume_rank(df: pd.DataFrame) -> pd.Series:
    """Cohort-rank spend onto one [0,1] axis: rank category-sum within the breakdown group,
    rank f5 within the no-breakdown group. Never raw f5 as primary volume (it's saturated)."""
    cats = df[SPEND_CATS].sum(axis=1, min_count=1)     # NaN if all categories missing
    has = cats.notna()
    out = pd.Series(np.nan, index=df.index)
    out[has] = cats[has].rank(pct=True)
    out[~has] = df.loc[~has, "f5"].rank(pct=True)      # fallback; NaN only if f5 also missing
    return out


def revenue_terms(df: pd.DataFrame) -> pd.DataFrame:
    """Each term a [0,1] rank; missing -> 0 (that revenue doesn't exist for the member)."""
    t = pd.DataFrame(index=df.index)
    t["spending"]    = spend_volume_rank(df)
    t["balance_int"] = _rank(df.f1)
    t["borrow_int"]  = df.f17.notna().astype(int) * _rank(df.f17)   # 0 for non-lenders
    t["depth"]       = _rank(df.f19.fillna(0) + df.f20.fillna(0))
    return t.fillna(0.0)


def cost_terms(df: pd.DataFrame) -> pd.DataFrame:
    """Each term a [0,1] rank; missing -> 0 (that cost doesn't exist for the member)."""
    redemption_intensity = df.f21 / (df.f4 + df.f21)               # [0,1]; low => breakage => cheaper
    benefit = df[["f13", "f14", "f15", "f16"]].sum(axis=1, min_count=1)
    t = pd.DataFrame(index=df.index)
    t["rewards_cost"]   = _rank(df.f21) + REWARDS_LAMBDA * _rank(df.f4) * (1 - redemption_intensity)
    t["perks_cost"]     = _rank(benefit)
    t["servicing_cost"] = df.f2.fillna(0)                          # already ~0/1
    return t.fillna(0.0)


def risk_factor(df: pd.DataFrame) -> pd.Series:
    """[0, cap): PD-like f11 (ranked) amplified by collection calls f3. Shaves the whole score."""
    r = RISK_A * _rank(df.f11) + RISK_B * df.f3.fillna(0)
    return r.fillna(0.0).clip(0, RISK_CAP)


def score(df: pd.DataFrame, weights: dict = WEIGHTS) -> pd.Series:
    """Profitability score per row: (Revenue − Cost) × (1 − Risk), weights keyed by segment."""
    seg = segment(df)
    rev_t, cost_t = revenue_terms(df), cost_terms(df)
    risk = risk_factor(df)
    rev = pd.Series(0.0, index=df.index)
    cost = pd.Series(0.0, index=df.index)
    for si, sname in enumerate(SEGMENTS):
        m = (seg == sname)
        for term in REV_TERMS:
            rev[m] += weights[term][si] * rev_t.loc[m, term]
        for term in COST_TERMS:
            cost[m] += weights[term][si] * cost_t.loc[m, term]
    return (rev - cost) * (1 - risk)
```

- [ ] **Step 4: Implement `_self_check` (insert above `main`) — the project-standard assert test**

```python
def _self_check():
    """Tiny hand-built frame: covers all 3 segments; a high-spend/low-risk member must outrank a
    tiny-spend/high-risk one; ranges stay comparable; scoring is deterministic."""
    demo = pd.DataFrame({
        "id":  [0, 1, 2, 3],
        "f1":  [0.0, 5000.0, 2000.0, 0.0],          # row1 revolver, row2 lender, row0/3 transactor
        "f2":  [0, 0, 0, 1], "f3": [0, 0, 0, 1],
        "f4":  [100000.0, 50000.0, 80000.0, 200000.0],
        "f5":  [12000.0, 3000.0, 6000.0, 400.0],
        "f6":  [10000.0, 2000.0, 4000.0, 80.0], "f7": [40000.0, 8000.0, 15000.0, 150.0],
        "f8":  [2000.0, 500.0, 900.0, 40.0], "f9": [2000.0, 500.0, 900.0, 40.0],
        "f10": [5000.0, 1000.0, 2000.0, 90.0],
        "f11": [0.01, 0.05, 0.03, 0.30], "f12": [20, 30, 25, 40],
        "f13": [1, 0, 1, 0], "f14": [50, 0, 30, 0], "f15": [5, 3, 4, 0], "f16": [60, 50, 55, 40],
        "f17": [np.nan, np.nan, 30000.0, np.nan], "f18": [np.nan, np.nan, 28000.0, np.nan],
        "f19": [2, 1, 2, 1], "f20": [2, 1, 2, 1], "f21": [80000.0, 10000.0, 40000.0, 5000.0],
        "f22": [5, 4, 4, 3], "f23": [np.nan, np.nan, np.nan, np.nan],
    })
    assert set(segment(demo)) == {"transactor", "revolver", "lender"}, segment(demo).tolist()
    rt, ct = revenue_terms(demo), cost_terms(demo)
    assert rt.notna().all().all() and ct.notna().all().all(), "terms must have no NaN after fill"
    assert (rt.to_numpy() >= 0).all() and (rt.to_numpy() <= 1.001).all(), "rev terms out of [0,1]"
    assert risk_factor(demo).between(0, RISK_CAP).all()
    s = score(demo)
    assert s.notna().all()
    assert s[0] > s[3], f"high-value row0 must outrank low-value row3: {s.round(3).tolist()}"
    assert score(demo).equals(score(demo)), "scoring must be deterministic"
    print("OK score.py self-checks pass:", s.round(3).tolist())
```

- [ ] **Step 5: Run the full module — self-checks pass, then it scores all 500K**

Run: `.venv/bin/python src/score.py`
Expected:
```
OK score.py self-checks pass: [...]
scored 500,000 rows -> .../data/scores_v1.csv
count    500000.0
...
```
Confirm: `data/scores_v1.csv` exists with 500,000 data rows, no blank scores.

- [ ] **Step 6: Eyeball business sanity (one command, no new code)**

Run: `.venv/bin/python -c "import sys; sys.path.insert(0,'src'); from eda import PremierEDA; from score import score, segment; df=PremierEDA().df; s=score(df); seg=segment(df); top=s>=s.quantile(0.8); print('top-20% segment mix:'); print(seg[top].value_counts(normalize=True).round(3)); print('overall mix:'); print(seg.value_counts(normalize=True).round(3))"`
Expected: prints both mixes. Sanity: the top-20% mix should not be ~100% one segment; lenders/revolvers (interest revenue) should be at least proportionally represented. If one segment is wholly absent from the top, the per-segment weights need revisiting before Task 2.

---

### Task 2: `src/validation.py` — top-20% stability (the label-free metric stand-in)

**Files:**
- Create: `src/validation.py`

**Interfaces:**
- Consumes: `from score import score, segment, WEIGHTS, SEED`; `from eda import PremierEDA`.
- Produces: a printed stability report + asserts. `subsample_stability(df) -> float`, `weight_perturbation_stability(df) -> float`, both in [0,1].

- [ ] **Step 1: Create `src/validation.py` with the report `main` + asserts, helpers not yet defined**

```python
"""Top-20% stability validation for the v1 score (label-free).

The real metric is % overlap of OUR top-20% vs Amex's hidden top-20%. With no label, we instead
prove our top-20% is STABLE — robust to which rows we see (subsample) and to the exact weights
(perturbation) — and business-plausible. Spec stage 7. NO submission until this looks healthy.

Run:  .venv/bin/python src/validation.py
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from eda import PremierEDA
from score import score, segment, WEIGHTS, SEED

TOP_Q = 0.8


def main():
    df = PremierEDA().df
    base = score(df)
    assert base.notna().all(), "base score has NaNs"
    sub = subsample_stability(df)
    wpt = weight_perturbation_stability(df)
    assert 0 <= sub <= 1 and 0 <= wpt <= 1
    top = base >= base.quantile(TOP_Q)
    print(f"subsample top-20% stability (Jaccard, mean): {sub:.3f}")
    print(f"weight-perturbation top-20% stability:       {wpt:.3f}")
    print(f"score concentration (Gini):                  {PremierEDA._gini(base):.3f}")
    print("top-20% segment mix:")
    print(segment(df)[top].value_counts(normalize=True).round(3))
    print("OK validation.py ran. Read the numbers before deciding on a submission.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it — verify it fails because the helpers don't exist yet**

Run: `.venv/bin/python src/validation.py`
Expected: FAIL — `NameError: name 'subsample_stability' is not defined`

- [ ] **Step 3: Implement the stability helpers (insert above `main`)**

```python
def top_set(s: pd.Series, q: float = TOP_Q) -> set:
    return set(s.index[s >= s.quantile(q)])


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a | b) else 1.0


def subsample_stability(df: pd.DataFrame, n: int = 20, frac: float = 0.7, seed: int = SEED) -> float:
    """Mean Jaccard of (top-20% ranked within a frac-subsample) vs (full-data top-20% ∩ that subsample).
    High => the top tail isn't an artifact of which rows happened to be scored."""
    rng = np.random.default_rng(seed)
    base_top = top_set(score(df))
    ov = []
    for _ in range(n):
        idx = rng.choice(df.index.to_numpy(), size=int(len(df) * frac), replace=False)
        sub_top = top_set(score(df.loc[idx]))
        base_top_in_sub = base_top & set(idx)
        ov.append(jaccard(sub_top, base_top_in_sub))
    return float(np.mean(ov))


def weight_perturbation_stability(df: pd.DataFrame, n: int = 15, pct: float = 0.15, seed: int = SEED) -> float:
    """Mean Jaccard of baseline top-20% vs top-20% after jittering every weight by ±pct.
    High => the ranking doesn't hinge on the exact (un-calibrated) weight values."""
    rng = np.random.default_rng(seed + 1)
    base_top = top_set(score(df))
    ov = []
    for _ in range(n):
        w = {k: tuple(max(0.0, x * (1 + rng.uniform(-pct, pct))) for x in v) for k, v in WEIGHTS.items()}
        ov.append(jaccard(base_top, top_set(score(df, w))))
    return float(np.mean(ov))
```

- [ ] **Step 4: Run the full report — helpers resolve, numbers print**

Run: `.venv/bin/python src/validation.py`
Expected (numbers will vary; shape is what matters):
```
subsample top-20% stability (Jaccard, mean): 0.7xx
weight-perturbation top-20% stability:       0.8xx
score concentration (Gini):                  0.xxx
top-20% segment mix:
lender       0.4xx
transactor   0.3xx
revolver     0.2xx
OK validation.py ran. ...
```
Interpretation gate (no hard pass/fail asserted — these are judgment numbers):
- **Subsample stability** healthy ≈ ≥0.65 (Jaccard on a 70% subsample is inherently bounded below 1).
- **Weight-perturbation** healthy ≈ ≥0.80 — if low, the un-calibrated weights are driving the ranking and calibration (stage 6) matters a lot.
- **Segment mix** should be plausible (no segment near 0% or near 100%).
Record these numbers in the experiment log before any submission decision.

---

## Self-Review

**Spec coverage** (`.claude/memory/framework-design.md`):
- Master equation `(Rev−Cost)×(1−Risk)` → Task 1 `score()`. ✓
- Segment tag (selects weights, no split) → Task 1 `segment()` + `WEIGHTS` keyed by segment. ✓
- Revenue terms (spending cohort-rank fallback, balance_int, borrow_int drop f18, depth) → Task 1 `revenue_terms`/`spend_volume_rank`. ✓
- Cost terms (rewards = f21 + breakage-discounted f4, perks, servicing) → Task 1 `cost_terms`. ✓
- Risk haircut (f11 ranked + f3, clamped, whole-score) → Task 1 `risk_factor`. ✓
- Missing → 0 contribution → `.fillna(0.0)` on terms + `has_lend_line` gate. ✓
- Output: continuous score per id, sorted → Task 1 `main()`. ✓
- Validation: top-20% stability (subsample + weight perturbation), Gini, segment sanity, no submission → Task 2. ✓

**Placeholder scan:** No TBD/TODO. Weight numbers are concrete v1 priors (deliberately tunable in stage 6), not placeholders.

**Type consistency:** `segment()` returns the exact `SEGMENTS` strings used to index `WEIGHTS` tuples in `score()`. `score(df, weights=WEIGHTS)` signature matches the perturbed-weights call in Task 2. `top_set`/`jaccard`/`score` names consistent across both files. ✓
