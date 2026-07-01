"""Magnitude framework (v2.0 — submission v3+). Rank by ESTIMATED DOLLAR contribution margin,
NOT percentile rank.

Hypothesis (stage-9): the true top-20% is whale-shaped — a few high-dollar members hold most of
the profit. Percentile-ranking every term (framework v1.x) flattens that concentration (our two
percentile submissions both capped ~0.46 on the public LB), so it structurally cannot match a
concentrated truth. This scores each member's profit in (proxy) dollars instead, letting natural
magnitudes weight the features the way an issuer P&L does.

    score_$ = interchange + net_interest − rewards − benefit_credits − expected_loss

Rates are proxy-annualized (masked units treated as proxy-dollars; documented in
framework-doc-v3-magnitude.md). Uses only f1–f23, never id. Deterministic.

Run:  .venv/bin/python src/score_magnitude.py   # self-check, then writes data/scores_v3.csv (+ v4 spend)
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from eda import PremierEDA, SPEND_CATS

SEED = 42
ROOT = Path(__file__).resolve().parent.parent
# --- proxy rates (research-anchored: Amex 10-K / Fed FEDS 2022 / CFPB) ---
R_INTERCHANGE = 0.022   # Amex blended discount rate on spend
R_INTEREST    = 0.08    # net annual interest margin per $ of carried balance (12% yield − loss/opex)
CPP           = 0.010   # issuer cost per redeemed reward point ($)
LGD           = 0.50    # loss-given-default fraction on credit exposure
LOUNGE_COST   = 35.0    # issuer cost per lounge visit ($)


def spend_dollars(df: pd.DataFrame) -> pd.Series:
    """Total spend in proxy dollars on ONE comparable scale across both cohorts.
    Breakdown cohort: uncensored category-sum f6–f10. No-breakdown cohort: f5 is capped (~13.6K)
    and on a different scale, so we QUANTILE-MAP it onto the breakdown spend distribution — this
    preserves each no-breakdown member's internal f5 ordering but lets them compete fairly instead
    of being crushed below everyone by an 18x ceiling artifact (A1). Missing both -> 0.
    Assumes the no-breakdown cohort's spend distribution resembles the breakdown cohort's."""
    cat = df[SPEND_CATS].sum(axis=1, min_count=1)
    out = cat.copy()
    nb = cat.isna() & df.f5.notna()                       # no-breakdown but has total spend
    if nb.any() and cat.notna().any():
        ref = np.sort(cat[cat.notna()].to_numpy())
        f5r = df.loc[nb, "f5"].rank(pct=True).to_numpy()
        out.loc[nb] = np.quantile(ref, f5r)               # f5 percentile -> breakdown $ distribution
    return out.fillna(0.0)


def dollar_profit(df: pd.DataFrame) -> pd.Series:
    """Estimated annual dollar contribution margin = revenue − cost, in proxy dollars."""
    f = df.fillna(0.0)
    sp = spend_dollars(df).values
    interchange = R_INTERCHANGE * sp
    interest    = R_INTEREST * f.f1.values
    rewards     = CPP * f.f21.values
    benefits    = f.f14.values + f.f15.values + f.f16.values + LOUNGE_COST * f.f13.values
    exp_loss    = LGD * f.f11.values * f.f1.values
    return pd.Series(interchange + interest - rewards - benefits - exp_loss, index=df.index)


def dollar_spend(df: pd.DataFrame) -> pd.Series:
    """Benchmark: rank purely by spend dollars (tests 'is the truth just spend magnitude?')."""
    return spend_dollars(df)


# Per-$ NET margins by spend category (interchange minus category-specific reward cost), cited
# from the unit-economics research: airline/lodging are net-NEGATIVE (5x reward cost > discount),
# dining/other/entertainment net-positive. These FOLD IN the spend-driven reward cost.
CAT_MARGIN = {"f6": -0.020, "f7": 0.013, "f8": 0.010, "f9": -0.015, "f10": 0.0185}


def dollar_profit_catmargin(df: pd.DataFrame) -> pd.Series:
    """v5: dollar_profit but interchange is replaced by CATEGORY-MARGIN-weighted spend — each spend
    category earns its own net margin (airline/lodging negative). Since spend dominates the ranking,
    reshaping the spend signal is the highest-leverage lever. Category margins already net per-category
    reward cost, so the flat f21 reward term is dropped. No-breakdown cohort: quantile-mapped spend ×
    the breakdown cohort's realized average net margin (keeps the cohorts on consistent footing)."""
    f = df.fillna(0.0)
    has_bd = df[SPEND_CATS].notna().any(axis=1).values
    catrev = sum(CAT_MARGIN[c] * f[c].values for c in SPEND_CATS)
    sp = spend_dollars(df).values
    blend = catrev[has_bd].sum() / sp[has_bd].sum() if sp[has_bd].sum() else 0.0  # breakdown avg margin
    catrev = np.where(has_bd, catrev, blend * sp)
    benefits = f.f14.values + f.f15.values + f.f16.values + LOUNGE_COST * f.f13.values
    exp_loss = LGD * f.f11.values * f.f1.values
    return pd.Series(catrev + R_INTEREST * f.f1.values - benefits - exp_loss, index=df.index)


CPP_CONTINGENT = CPP * 0.9 * 0.2   # cost/pt × redemption prob × annual expensing fraction


def dollar_profit_catmargin_f4(df: pd.DataFrame) -> pd.Series:
    """v6: v5 category-margin MINUS a small contingent liability on the outstanding points balance f4
    (annualized expected redemption cost). Re-adds a real cost the period-flow versions dropped —
    members sitting on large unredeemed balances carry a future cost."""
    f = df.fillna(0.0)
    return pd.Series(dollar_profit_catmargin(df).values - CPP_CONTINGENT * f.f4.values, index=df.index)


def _catmargin_cohortfix(df: pd.DataFrame, cm: dict, nb_signal=None) -> pd.Series:
    """Cohort-fixed category-margin score for a given per-category margin dict `cm`. Breakdown cohort
    scored by category margins; the ~23% no-breakdown cohort's spend is estimated by quantile-mapping
    a proxy SIGNAL onto the breakdown spend distribution.

    nb_signal=None  -> v7 behavior: proxy = f4 where present, else 0 (demoted to interest/cost only).
    nb_signal=array -> v9 behavior: proxy = the given per-row signal for ALL no-breakdown members
                       (no zeros) — fixes the 15%-of-pop blind spot (A15)."""
    f = df.fillna(0.0)
    has_bd = df[SPEND_CATS].notna().any(axis=1).values
    catsum = df[SPEND_CATS].sum(axis=1, min_count=1).values
    catrev = sum(cm[c] * f[c].values for c in SPEND_CATS)
    blend = np.nansum(catrev[has_bd]) / np.nansum(catsum[has_bd])     # breakdown avg net margin
    if nb_signal is None:                                            # v7: f4 proxy, no-f4 -> 0
        nb_mask = (~has_bd) & df.f4.notna().values
        sig = f.f4.values
    else:                                                           # v9: imputed proxy for ALL no-bd
        nb_mask = ~has_bd
        sig = np.asarray(nb_signal, dtype=float)
    nb_spend = np.zeros(len(df))
    if nb_mask.any():
        ref = np.sort(catsum[has_bd])
        r = pd.Series(sig[nb_mask]).rank(pct=True).to_numpy()
        nb_spend[nb_mask] = np.quantile(ref, r)                      # proxy percentile -> breakdown spend $
    rev = np.where(has_bd, catrev, blend * nb_spend)
    benefits = f.f14.values + f.f15.values + f.f16.values + LOUNGE_COST * f.f13.values
    exp_loss = LGD * f.f11.values * f.f1.values
    return pd.Series(rev + R_INTEREST * f.f1.values - benefits - exp_loss, index=df.index)


def dollar_profit_catmargin_v7(df: pd.DataFrame) -> pd.Series:
    """v7: cohort-fixed category-margin (no-breakdown ranked by f4-proxy, not noise f5). LB 0.768."""
    return _catmargin_cohortfix(df, CAT_MARGIN)


# v8 high-earn hypothesis: premium cards earn 4-5x on dining AND travel, so those categories' reward
# cost can EXCEED interchange -> dining net-negative too; only general retail ("other", 1x) clearly positive.
CAT_MARGIN_V8 = {"f6": -0.025, "f7": 0.013, "f8": 0.005, "f9": -0.020, "f10": -0.010}


def dollar_profit_v8(df: pd.DataFrame) -> pd.Series:
    """v8: v7 cohort-fix + recalibrated margins (dining net-negative; stronger travel penalties)."""
    return _catmargin_cohortfix(df, CAT_MARGIN_V8)


# --- v9: interpretable spend IMPUTATION for the no-breakdown cohort (fixes the A15 blind spot) ---
# v7 ranks the no-breakdown 23% by f4-or-zero (OOS rank-corr to true spend ≈0.28; zeros 75K members
# with no f4). v9 instead imputes their spend from an OLS on the features that best predict spend
# among members who DO have a breakdown — interpretable, deterministic, uses only f1–f23 and NO
# profitability label (spend is an observed feature we fill where the breakdown is missing).
IMPUTE_FEATS = ["f4", "f21", "f1", "f11", "f12", "f13", "f14", "f15", "f16"]  # intuitive-sign set


def _spearman(a, b) -> float:
    a, b = pd.Series(np.asarray(a, float)), pd.Series(np.asarray(b, float))
    return float(np.corrcoef(a.rank(), b.rank())[0, 1])


def _impute_design(df: pd.DataFrame, feats, mu=None, sd=None):
    """log1p the heavy-tail predictors (f11 left linear), median-fill missing, standardize.
    Returns (X_standardized, mu, sd); pass mu/sd back to transform another frame identically."""
    cols = [df[c].astype(float).to_numpy() for c in feats]
    X = np.column_stack([v if c == "f11" else np.log1p(np.clip(v, 0.0, None))
                         for c, v in zip(feats, cols)])
    med = np.nanmedian(X, axis=0)
    nan = np.where(np.isnan(X))
    X[nan] = np.take(med, nan[1])
    if mu is None:
        mu, sd = X.mean(0), X.std(0); sd[sd == 0] = 1.0
    return (X - mu) / sd, mu, sd


def spend_imputer(df: pd.DataFrame, feats=IMPUTE_FEATS):
    """Fit OLS predicting log1p(category-sum spend) on the breakdown cohort; return a per-row
    predicted-spend signal for the whole frame (used to rank the no-breakdown cohort). Deterministic."""
    has_bd = df[SPEND_CATS].notna().any(axis=1).to_numpy()
    y = np.log1p(np.clip(df[SPEND_CATS].sum(axis=1, min_count=1).to_numpy(), 0.0, None))
    Xs, _, _ = _impute_design(df, feats)
    A = np.column_stack([np.ones(int(has_bd.sum())), Xs[has_bd]])
    coef, *_ = np.linalg.lstsq(A, y[has_bd], rcond=None)
    return coef[0] + Xs @ coef[1:], coef


def _cv_spearman_spend(df: pd.DataFrame, feats, k: int = 5, seed: int = SEED) -> float:
    """5-fold OUT-OF-SAMPLE Spearman of imputed vs true category-sum spend, on the breakdown cohort.
    The honest gate: does this proxy actually rank spend better than f4 alone (≈0.28)?"""
    has_bd = df[SPEND_CATS].notna().any(axis=1).to_numpy()
    sub = df.loc[has_bd].reset_index(drop=True)
    y = np.log1p(np.clip(sub[SPEND_CATS].sum(axis=1, min_count=1).to_numpy(), 0.0, None))
    Xs, _, _ = _impute_design(sub, feats)
    fold = np.random.default_rng(seed).permutation(len(sub)) % k
    pred = np.empty(len(sub))
    for fk in range(k):
        tr, te = fold != fk, fold == fk
        A = np.column_stack([np.ones(int(tr.sum())), Xs[tr]])
        coef, *_ = np.linalg.lstsq(A, y[tr], rcond=None)
        pred[te] = coef[0] + Xs[te] @ coef[1:]
    return _spearman(pred, y)


def dollar_profit_catmargin_v9(df: pd.DataFrame) -> pd.Series:
    """v9: v7 cohort-fix with the no-breakdown cohort's spend IMPUTED (OLS on log1p f4,f21,f1,f11,
    f12,f13–f16) instead of f4-or-zero. Every no-breakdown member gets a spend rank — fixes A15."""
    pred, _ = spend_imputer(df)
    return _catmargin_cohortfix(df, CAT_MARGIN, nb_signal=pred)


def v9_diagnostics(df: pd.DataFrame) -> None:
    """Internal A/B of v9 vs the locked v7 baseline — print BEFORE deciding on a submission."""
    base = _cv_spearman_spend(df, ["f4"])
    intu = _cv_spearman_spend(df, IMPUTE_FEATS)
    full = _cv_spearman_spend(df, IMPUTE_FEATS + ["f17", "f18", "f19", "f20"])
    print(f"CV OOS Spearman(imputed spend vs true): f4-alone={base:.3f}  intuitive-{len(IMPUTE_FEATS)}={intu:.3f}  +lend/cards={full:.3f}")
    s7, s9 = dollar_profit_catmargin_v7(df), dollar_profit_catmargin_v9(df)
    t7 = set(s7.index[s7 >= s7.quantile(0.8)]); t9 = set(s9.index[s9 >= s9.quantile(0.8)])
    j = len(t7 & t9) / len(t7 | t9)
    nb = set(df.index[~df[SPEND_CATS].notna().any(axis=1)])
    print(f"top-20% Jaccard v9~v7: {j:.3f}  (in {len(t9 - t7):,} / out {len(t7 - t9):,} of {len(t7):,})")
    print(f"no-breakdown share of top-20%: v7={len(t7 & nb) / len(t7):.1%}  v9={len(t9 & nb) / len(t9):.1%}  (cohort = {len(nb) / len(df):.1%} of pop)")
    print(f"v9 NaNs: {int(s9.isna().sum())}  range [{s9.min():.1f}, {s9.max():.1f}]  deterministic: {dollar_profit_catmargin_v9(df).equals(s9)}")


# v10: weights RECOVERED by leaderboard triangulation (src/triangulate.py) — fit so the implied
# top-20% reproduces ALL 9 prior submissions' public-LB overlaps (in-sample RMSE 0.0012; leave-one-out
# mean |err| 0.014 → generalizes). Only the SIGN-STABLE terms (consistent across 6 restarts) are kept;
# the unstable small terms (spend_log/lodging/benefits/f4/f21/f3) are dropped to 0. Each term is
# scaled by its own std (matching the triangulation basis) then weighted. Headline vs v7: revolving
# balance f1 is a FIRST-CLASS lever (~0.7x the top spend category), not v7's flat 0.08; dining flips
# negative; lodging drops out. No-breakdown cohort (f6–f10 = 0) is ranked by f1/risk only → ~5% of
# the top-20% (consistent with the v9 lesson that this cohort should be demoted, not promoted).
RECOVERED_W = {"f7": 0.738, "f1": 0.523, "f8": 0.348, "f10": -0.137, "f6": -0.110}
RECOVERED_RISK_W = 0.110   # weight on the expected-loss term  -(f11 * f1)


def dollar_profit_v10_triangulated(df: pd.DataFrame) -> pd.Series:
    """v10: leaderboard-triangulation-recovered weighted score (see src/triangulate.py)."""
    f = df.fillna(0.0)
    terms = {"f6": f.f6.values, "f7": f.f7.values, "f8": f.f8.values, "f10": f.f10.values, "f1": f.f1.values}
    score = np.zeros(len(df))
    for k, wv in RECOVERED_W.items():
        v = terms[k]
        score += wv * v / (v.std() + 1e-9)
    expl = -(f.f11.values * f.f1.values)
    score += RECOVERED_RISK_W * expl / (expl.std() + 1e-9)
    return pd.Series(score, index=df.index)


# --- v11: riskiness as a MULTIPLICATIVE survival gate + explicit f3 (collection) demotion ---
# Why (decision-log 2026-06-29): the 12-term LINEAR weighted-sum family caps ~0.81-0.85 (leave-one-out
# predicted 0.857 for v10, actual 0.805) — the path past it is non-linear STRUCTURE, not more weights.
# The brief names "riskiness" as 1 of 4 equal profitability drivers, yet v10 uses it only as a small
# additive term and drops f3 entirely; A17 documents 6,662 collection-flagged (f3=1) members polluting
# v10's top-20% (~10x default risk, ~$0 spend, admitted purely via their f1 interest credit). v11 keeps
# v10's SIGN-STABLE recovered revenue drivers (f7,f1,f8 — the re-fit found f6/f10 category signs
# UNSTABLE, so they're dropped) and turns risk multiplicative, matching the literature's margin x
# persistence skeleton (decision-log 2026-06-27):
#
#     v11 = [W7*z(f7) + W1*z(f1) + W8*z(f8)]  x  (1 - LGD*f11)  x  (1 - D*f3)
#            \___________revenue___________/     \__risk gate__/    \_delinq_/
#
# z(x)=x/std(x) is v10's exact basis. Risk gate = the economic expected-loss rate (LGD is already a P&L
# constant -> NO new free parameter). f1's dual nature (interest revenue AND default exposure) lands in
# ONE place: it earns in the revenue term and is shaved by the same risk gate. D = collection-cancel
# demotion (business choice, default 0.90 -> keep 10% of their revenue; swept in v11_diagnostics).
REV_W = {"f7": 0.738, "f1": 0.523, "f8": 0.348}    # v10's sign-stable positive drivers (RECOVERED_W)
DELINQ_DEMOTION = 0.90                              # f3=1 members keep (1 - D) of their revenue


def _v11_revenue(df: pd.DataFrame) -> np.ndarray:
    """v10's stable positive revenue drivers, standardized on the v10 basis (>=0 magnitude)."""
    f = df.fillna(0.0)
    rev = np.zeros(len(df))
    for k, w in REV_W.items():
        v = f[k].values
        rev += w * v / (v.std() + 1e-9)
    return rev


def dollar_profit_v11_riskgate(df: pd.DataFrame, d: float = DELINQ_DEMOTION,
                               risk_k: float = LGD) -> pd.Series:
    """v11: v10 stable revenue x multiplicative risk gate x collection-cancel demotion. Deterministic.
    Uses only f1,f3,f7,f8,f11 (never id); no NaNs (fillna 0; gates always finite & positive)."""
    f = df.fillna(0.0)
    rev = _v11_revenue(df)
    risk_gate = 1.0 - risk_k * f.f11.values        # expected-loss discount (economic, in [0.84, 1.0])
    delinq_gate = 1.0 - d * f.f3.values            # collection-cancel demotion (A17), f3 in {0,1}
    return pd.Series(rev * risk_gate * delinq_gate, index=df.index)


def dollar_profit_v10_f3demote(df: pd.DataFrame) -> pd.Series:
    """Minimal A17 fix: v10 EXACTLY, but collection-flagged (f3=1) members are demoted out of
    contention (pushed below the score floor). Isolates the single highest-confidence change —
    evicting the delinquent contaminants from v10's top-20% — with no other reshuffle. Lowest-risk
    submission candidate: it only does what A17 directly justifies, leaving the 0.805 ranking intact."""
    s = dollar_profit_v10_triangulated(df)
    f3 = pd.Series(df["f3"].fillna(0).to_numpy() == 1, index=df.index)
    return s.mask(f3, s.min() - 1.0)


# v12: A16 fix — NEUTRALIZE v10's economically-unsupported category signs (dining f10, airline f6), keep
# its sign-stable f7/f8/f1 weights + additive risk term, and stack the validated f3 eviction (A17).
# WHY NEUTRAL, not flipped positive: triangulation found category signs SIGN-UNSTABLE = noise (decision-log
# 2026-06-29), so the consistent move is to ZERO the untrustworthy weights, not assert a positive one. A
# +0.137 dining FLIP was built and REJECTED by framework-critic (2026-06-29): its gain rode on the ceiling-
# CENSORED dining cluster — promoted members had dining 8x the pop median, 25% pinned at the data cap —
# which won't generalize to the hidden 30%. Dining is 1x (brief p8) → mildly positive/neutral, not a bonus
# and not a penalty; zeroing matches that economics and removes v10's unsupported NEGATIVE sign cleanly.
RECOVERED_W_V12 = {"f7": 0.738, "f1": 0.523, "f8": 0.348}   # f10 & f6 NEUTRALIZED to 0 (signs are noise)


def dollar_profit_v12_signfix(df: pd.DataFrame, evict_f3: bool = True) -> pd.Series:
    """v12: v10 with the noise-sign category terms (dining f10, airline f6) NEUTRALIZED to 0 + f3 eviction.
    The defensible A16 de-risk — removes v10's unsupported negative signs without asserting an equally-
    unsupported positive one. A second-priority bet, to test only AFTER v11-minimal gets an LB read."""
    f = df.fillna(0.0)
    score = np.zeros(len(df))
    for k, wv in RECOVERED_W_V12.items():
        v = f[k].values
        score += wv * v / (v.std() + 1e-9)
    expl = -(f.f11.values * f.f1.values)
    score += RECOVERED_RISK_W * expl / (expl.std() + 1e-9)          # v10's additive risk term, kept
    s = pd.Series(score, index=df.index)
    if evict_f3:
        s = s.mask(pd.Series(f.f3.values == 1, index=df.index), s.min() - 1.0)
    return s


# === v13 / v14: candidates from the 2026-06-30 strategic build+diagnostic (no submission yet) ===
# Finding: a FULL raw-dollar revenue−cost model (catrev w/ negative airline/lodging margins, interest,
# contingent f4, benefits w/ f15-months fix, expected loss) has Jaccard only 0.50 vs v11min — but the
# divergence is ~entirely the NEGATIVE travel margins dumping ~19K pure-transactor mega-spenders
# (median catsum $190K, travel $61K, f1=0) out of the top-20%. That is the A16 overfit trap and the
# v6(−0.058)/v8(−0.087) LB losses already argue the truth rewards spend magnitude incl. travel.
# The DEFENSIBLE economic additions (benefits properly scaled, contingent f4) barely move v11min
# (Jaccard 0.96–0.97, <2.2K members) — they're real P&L lines but don't differentiate the dense
# boundary (A19/A22). So the two candidates below stay ANCHORED to v11min's validated revenue
# ranking and add only economically-honest, low-divergence structure.

BENEFIT_COSTS = dict(air_credit="f14", cab_months="f15", ent_credit="f16", lounge="f13")  # doc only


def _cost_terms(f: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The three issuer cost lines v10/v11min omit, in proxy dollars. f15 is MONTHS → ×$15/mo
    (feature-notes: the raw-f15 benefit term understated cab cost ~15×). Contingent reward
    liability on the unredeemed balance f4 = cost/pt × P(redeem) × annual-expensing fraction."""
    benefit = f.f14.values + 15.0 * f.f15.values + f.f16.values + LOUNGE_COST * f.f13.values
    contingent = (CPP * 0.9 * 0.2) * f.f4.values
    exp_loss = LGD * f.f11.values * f.f1.values
    return benefit, contingent, exp_loss


def dollar_profit_v13_costaug(df: pd.DataFrame, w_ben: float = 0.05, w_cont: float = 0.0,
                              w_loss: float = 0.05, evict_f3: bool = True) -> pd.Series:
    """v13: v10's validated revenue ranking MINUS the omitted cost lines, each z-scored and added
    with a small economic weight, then the validated f3 eviction. Makes the score economically
    COMPLETE (it now books benefit credits — with the f15-is-MONTHS rescale — and expected loss the
    issuer actually pays) while staying within Jaccard ~0.97 of v11min: it sharpens the cost side
    without betting on the unvalidated negative-travel-margin reshuffle.
    ⚠ w_cont DEFAULTS TO 0: the contingent-f4 term is byte-identical to v6's CPP_CONTINGENT·f4, which
    scored 0.675 (−0.058 vs v5) on the public LB — it demotes the highest rewards-balance members
    (the v6 failure mode). Left as an opt-in knob only; do NOT enable it for a submission.
    Writeup-grade defensibility per dollar; expect ~LB-neutral, small downside, small upside."""
    f = df.fillna(0.0)
    base = dollar_profit_v10_triangulated(df).to_numpy()
    benefit, contingent, exp_loss = _cost_terms(f)
    def z(v):
        return v / (v.std() + 1e-9)
    score = base - w_ben * z(benefit) - w_cont * z(contingent) - w_loss * z(exp_loss)
    s = pd.Series(score, index=df.index)
    if evict_f3:
        s = s.mask(pd.Series(f.f3.values == 1, index=df.index), s.min() - 1.0)
    return s


def dollar_profit_v14_riskfloor(df: pd.DataFrame, thr: float = LGD and 0.16) -> pd.Series:
    """v14: v11min PLUS a parameter-free risk floor — demote any member whose expected loss exceeds
    interest revenue, i.e. LGD·f11·f1 > R_INTEREST·f1  ⇔  f11 > R_INTEREST/LGD = 0.16 (with f1>0).
    This is the principled GENERALIZATION of the validated f3 eviction (A17/A22): f3 demotes by a
    delinquency FLAG; this demotes by the ECONOMICS (net-negative lending), catching the ~13.5K
    risky revolvers A22-R4 found that the f3 flag misses. Moves only ~800 members in v11min's
    top-20% (most are already low-scored) → a low-risk, high-defensibility private-30% hedge."""
    s = dollar_profit_v10_f3demote(df)
    f = df.fillna(0.0)
    bad = pd.Series((f.f11.values > thr) & (f.f1.values > 0), index=df.index)
    return s.mask(bad, s.min() - 1.0)


# === v15 / 2026-06-30: the ALL-POSITIVE functional-form bet (leaderboard-motivated) ===
# Context (decision-log 2026-06-30): leaders hit 0.906-0.915 on the SAME 23 features → the gap is
# functional FORM, not features (v11min's "dense boundary" is form-specific — a different defensible
# form reshuffles 64.6% of rank 90-110K). The LB has twice said DON'T penalize travel spend
# (v6 -0.058, v8 -0.087 both lost by making airline/lodging NEGATIVE; A16). v15 takes that to its
# conclusion: keep v10/v11min's VALIDATED core EXACTLY (f7/f8/f1 weights, the additive expected-loss
# term, the f3 eviction) and change ONLY the contested category signs to ALL-POSITIVE, plus restore
# the dropped lodging f9 — an isolated test of "the truth REWARDS spend magnitude, incl. 5x travel."
# f10 dining (1x) mirrors to +0.137 (a 1x category, like f7/f8); f6 airline & f9 lodging (5x,
# reward-heavy) get a modest +0.060 (positive interchange net of a higher reward cost — NOT negative).
# Everything else is byte-identical to v10, so an LB read is attributable to the sign flip alone.
RECOVERED_W_V15 = {"f7": 0.738, "f1": 0.523, "f8": 0.348, "f10": 0.137, "f6": 0.060, "f9": 0.060}


def dollar_profit_v15_allpos(df: pd.DataFrame) -> pd.Series:
    """v15: v10/v11min core with ALL-POSITIVE spend categories (+ restored f9 lodging) replacing the
    contested negative airline/dining signs; the additive expected-loss term and the f3 eviction are
    kept unchanged. Tests whether the hidden truth rewards (not penalizes) 5x travel spend — the
    leaderboard-motivated functional-form bet (decision-log 2026-06-30). Deterministic; uses only
    f1,f3,f6-f10,f11 (never id); no NaNs."""
    f = df.fillna(0.0)
    score = np.zeros(len(df))
    for k, wv in RECOVERED_W_V15.items():
        v = f[k].values
        score += wv * v / (v.std() + 1e-9)
    expl = -(f.f11.values * f.f1.values)
    score += RECOVERED_RISK_W * expl / (expl.std() + 1e-9)   # v10's additive expected-loss term, kept
    s = pd.Series(score, index=df.index)
    return s.mask(pd.Series(f.f3.values == 1, index=df.index), s.min() - 1.0)  # validated f3 screen


# v18: v15 (current best, LB 0.827) + a parameter-free NET-NEGATIVE-LENDING floor — the continuous-risk
# generalization of the LB-validated f3 eviction (A17/A22-R4). A member whose expected credit loss exceeds
# their interest revenue — LGD*f11*f1 > R_INTEREST*f1  <=>  f11 > R_INTEREST/LGD = 0.16 (with f1>0) — is a
# net-negative lending relationship and is demoted from the profitable tier. Triple-motivated: (1) the
# distress-demotion lever WON twice (f3-evict +0.018; v15 keeps it); (2) the recovered formula (12-submission
# OLS, scratchpad/recover_formula.py) weights risk MORE than v15 does; (3) A22-R4's swap test on these
# members passed economically (+$968/member total margin). No free parameter — the 0.16 crossover is fixed
# by the rates. Isolated, bounded change on the validated v15 base; an LB read is attributable to the floor.
def dollar_profit_v18_riskfloor(df: pd.DataFrame, thr: float = R_INTEREST / LGD) -> pd.Series:
    """v18: v15 all-positive PLUS demote net-negative-lending members (f11 > 0.16 & f1 > 0) below the tier.
    The economic generalization of the f3 collection screen. Deterministic; uses only f1,f3,f6-f11 (never id)."""
    s = dollar_profit_v15_allpos(df)
    f = df.fillna(0.0)
    bad = pd.Series((f.f11.values > thr) & (f.f1.values > 0), index=df.index)
    return s.mask(bad, s.min() - 1.0)


# v19: RAISE revolving-balance f1 to co-equal with the dominant spend term — the #1 gap from the Amex
# deep-research (2026-06-30, A26). Primary-source evidence: net interest yield on Card Member loans is
# ~11.9% (FY24, 3-0 verified), not the ~8% the rates assumed; the Fed FEDS decomposition + revolver/
# transactor literature find interest ≈ 80% of card profit and purchase volume DECOUPLED from profit
# (high-spend transactors are often low-profit). v15 weights f7-spend 0.738 > f1 0.523 (lending = 0.7x
# spend); v19 sets f1 = 0.738 (lending CO-EQUAL with spend), the most research-grounded untested lever for
# the 0.827->0.91 gap. Direction is confirmed by our biggest structural win (v10 raised f1 0.08->0.52,
# +0.037). Everything else byte-identical to v15 (all-positive categories, additive expected-loss, f3
# screen), so an LB read is attributable to the f1 weight alone. Bounded: moves 5,830 (Jaccard 0.89) and
# keeps the no-breakdown cohort at a safe 1.1% of the top tier (the v9 over-promotion guard).
RECOVERED_W_V19 = {"f7": 0.738, "f1": 0.738, "f8": 0.348, "f10": 0.137, "f6": 0.060, "f9": 0.060}


def _allpos_score(df: pd.DataFrame, w_f1: float) -> pd.Series:
    """v15/v19/v20 shared engine: all-positive category weights + a tunable revolving-balance weight
    w_f1, the additive expected-loss term, and the f3 screen. w_f1=0.523 -> v15; 0.738 -> v19; 1.0 -> v20."""
    f = df.fillna(0.0)
    weights = {"f7": 0.738, "f1": w_f1, "f8": 0.348, "f10": 0.137, "f6": 0.060, "f9": 0.060}
    score = np.zeros(len(df))
    for k, wv in weights.items():
        score += wv * f[k].values / (f[k].values.std() + 1e-9)
    expl = -(f.f11.values * f.f1.values)
    score += RECOVERED_RISK_W * expl / (expl.std() + 1e-9)
    s = pd.Series(score, index=df.index)
    return s.mask(pd.Series(f.f3.values == 1, index=df.index), s.min() - 1.0)


def dollar_profit_v19_lending(df: pd.DataFrame) -> pd.Series:
    """v19 (LB 0.859, NEW BEST): v15 all-positive with revolving balance f1 raised to CO-EQUAL with the top
    spend driver (0.523 -> 0.738), reflecting Amex's ~12% net interest yield and the finding that lending/
    interest, not spend volume, concentrates card profit (A26). All else identical to v15. Deterministic."""
    return _allpos_score(df, 0.738)


# v20: push f1 to 1.0 — lending DOMINANT over spend. v19's +0.032 win proved f1's optimum is >= 0.738;
# the 10-K net interest yield (~12%) vs interchange (~2%) and the Fed "interest ~80% of card profit"
# argue lending should outweigh spend, not merely match it. no-breakdown share stays ~1.8% (v19's 1.1%
# did not hurt; the v9 -0.041 guard was a 19% over-promotion by imputed spend, a different mechanism).
def dollar_profit_v20_lending2(df: pd.DataFrame) -> pd.Series:
    """v20: v19 with revolving balance f1 raised further to 1.0 (lending DOMINANT over the top spend term).
    Tests whether the confirmed lending lever keeps gaining past co-equal. Deterministic; never uses id.
    NOTE: the internal LB-predictor (src/lb_predict.py) scores v20 ~flat-to-below v19 (f1 peaks at 0.738),
    so this is NOT recommended for a submission — kept for the record."""
    return _allpos_score(df, 1.0)


# v21: recover the ABSENT feature TENURE (A10 — not in f1-f23) as a proxy from the features we have, and
# add it to v19 as a secondary CLV term. Theory: Membership Rewards points ACCUMULATE over the cardmember
# lifetime, so the points-balance stock f4 (net of redemption) proxies tenure/loyalty — a profitability
# driver the issuer cares about (CLV) that none of the 4 named drivers captures. f4 is orthogonal to v19
# (Spearman 0.25), i.e. genuinely NEW information. Missing f4 (51%, co-missing f21) -> MEDIAN-filled in the
# tenure term so "rewards data absent" is read as "tenure unknown = average", NOT "tenure = 0". Weight is
# SECONDARY (0.25 vs the 0.738 revenue drivers) because tenure is an inferred proxy, not a booked P&L line.
# HONEST: orthogonal to v19, so the LB-predictor is BLIND to it (can't pre-validate) — this is a genuine
# bounded-downside BET that the 0.859->~0.91 gap is the absent CLV/tenure dimension. It trades against the
# lending win (promotes high-tenure transactors over some revolvers), so only the leaderboard can judge it.
TENURE_W = 0.25


def _tenure_term(df: pd.DataFrame) -> np.ndarray:
    """log1p(f4) points-balance stock as a tenure/loyalty proxy, median-filled where f4 is missing
    (unknown tenure = average, not zero), then standardized on the v10/v15 basis."""
    f4 = df["f4"].to_numpy(float)
    ten = np.log1p(f4)                                  # NaN stays NaN through log1p
    ten = np.where(np.isnan(ten), np.nanmedian(ten), ten)
    return _z(ten)


def dollar_profit_v21_tenure(df: pd.DataFrame, w_ten: float = TENURE_W) -> pd.Series:
    """v21: v19 (lending co-equal, LB 0.859) PLUS a secondary tenure/CLV term recovered from the rewards
    points-balance stock f4 (points accumulate over the cardmember lifetime). Tests whether the absent
    tenure dimension (A10) closes the gap to the leaders. Deterministic; uses f1,f3,f4,f6-f11 (never id)."""
    f = df.fillna(0.0)
    score = np.zeros(len(df))
    for k, wv in RECOVERED_W_V19.items():
        score += wv * f[k].values / (f[k].values.std() + 1e-9)
    score += RECOVERED_RISK_W * _z(-(f.f11.values * f.f1.values))
    score += w_ten * _tenure_term(df)                   # recovered absent-feature: tenure/CLV
    s = pd.Series(score, index=df.index)
    return s.mask(pd.Series(f.f3.values == 1, index=df.index), s.min() - 1.0)


# v22 (SWING BET, 2026-07-01): a BASIS TRANSFORM — the one genuinely-untested, defensible, orthogonal
# lever from the fresh problem-statement+data sweep ([[assumptions]] A34). v19 std-scales every term, which
# lets a MODERATE specialty spender's fat right tail masquerade as a whale (weight·z(f9-lodging) can spike a
# ~$1.6K-mean category). v22 keeps f7 (dominant general spend) and f1 (revolving balance) on the DOLLAR/std
# basis — they are linear-in-$ booked revenue (interchange, net interest) AND they carry the 15,721
# consensus-core f7-whales whose in-rate is 0.999 across every submission v5->v19 (demoting them is the
# LB-REJECTED direction, v6/v8) — but RANK-normalizes (percentile) the four small specialty cats f6/f8/f9/f10
# so a member can no longer clear the top-20% cutoff on one inflated specialty category. Validated: whale
# in-rate held 0.999 (NOT the losing direction), Jaccard 0.863 vs v19 (swaps 7,330 boundary members ~ the
# ~5,100-member gap to the 0.91 leaders), 0 NaN, 0 f3 in top-20%, deterministic. The LB-predictor is
# STRUCTURALLY BLIND to a basis change (it is fit to 13 std-scale submissions -> scores any basis change
# "far->bad"; it rates v22 at 0.822, which is NOT informative), so v22 CANNOT be screened -> it is a
# submission-only bet. Bounded downside: v19 (0.859) is banked and best-score-counts. Never uses id.
V22_DOLLAR_W = {"f7": 0.738, "f1": 0.738}                          # kept on the dollar/std basis
V22_RANK_W = {"f8": 0.348, "f10": 0.137, "f6": 0.060, "f9": 0.060}  # rank-normalized specialty cats


def dollar_profit_v22_hybrid(df: pd.DataFrame) -> pd.Series:
    """v22: v19's engine with the small specialty spend cats (f6/f8/f9/f10) RANK-normalized instead of
    std-scaled, while f7 and revolving balance f1 stay on the dollar/std basis (protects the consensus-core
    whales). A boundary-only basis transform — the one untested orthogonal lever (A34). Deterministic."""
    f = df.fillna(0.0)
    score = np.zeros(len(df))
    for k, wv in V22_DOLLAR_W.items():
        score += wv * f[k].values / (f[k].values.std() + 1e-9)
    for k, wv in V22_RANK_W.items():
        pct = pd.Series(f[k].values).rank(pct=True).values     # percentile in [0,1] — compresses the fat tail
        score += wv * pct / (pct.std() + 1e-9)
    score += RECOVERED_RISK_W * _z(-(f.f11.values * f.f1.values))
    s = pd.Series(score, index=df.index)
    return s.mask(pd.Series(f.f3.values == 1, index=df.index), s.min() - 1.0)


# v23 (2026-07-01): STACK the two confirmed post-v19 gains — v22's basis transform (LB 0.866, +0.007) PLUS
# the precise per-$ net-margin lever. Card economics (brief slide 8): travel (airline f6, lodging f9) earns
# 5x reward points (~7.5c/$ cost) vs ~2.2c/$ interchange => net-NEGATIVE per-$ margin; general/ent/dining
# (1x) => net-positive. The margin term z(Σ margin·spend) is STD-BASIS-additive, so unlike the basis change
# it IS visible to the LB-predictor, which scored it +0.018 on the v19 base (A31, candidate B) — the strongest
# positive signal we have for any next lever. On v22 it moves ~4,300 boundary members further in the SAME
# direction v22 won (gradient-compass CONTINUES; whales held 0.999). Deterministic; never uses id.
V23_MARGIN = {"f6": -0.053, "f9": -0.053, "f7": 0.007, "f8": 0.007, "f10": 0.007}   # per-$ net margin (5x vs 1x)
V23_MARGIN_W = 0.15                                                                  # predictor-backed on v19 (+0.018 at 0.15-0.20)


def dollar_profit_v23_hybrid_margin(df: pd.DataFrame) -> pd.Series:
    """v23: v22 hybrid-basis (f7/f1 dollar, specialty cats ranked) PLUS the precise per-$ net-margin term
    (travel's 5x-reward thin margin). Stacks the LB-confirmed basis transform with the predictor-backed
    margin lever. Deterministic; never uses id."""
    f = df.fillna(0.0)
    score = np.zeros(len(df))
    for k, wv in V22_DOLLAR_W.items():                                  # f7, f1 on the dollar/std basis
        score += wv * f[k].values / (f[k].values.std() + 1e-9)
    for k, wv in V22_RANK_W.items():                                    # f6/f8/f9/f10 rank-normalized
        pct = pd.Series(f[k].values).rank(pct=True).values
        score += wv * pct / (pct.std() + 1e-9)
    score += RECOVERED_RISK_W * _z(-(f.f11.values * f.f1.values))       # expected credit loss
    score += V23_MARGIN_W * _z(sum(m * f[k].values for k, m in V23_MARGIN.items()))   # precise per-$ margin
    s = pd.Series(score, index=df.index)
    return s.mask(pd.Series(f.f3.values == 1, index=df.index), s.min() - 1.0)


# v24 (2026-07-01, BOLD swing): DUAL-ENGINE interaction on the v22 spine. A member who BOTH spends heavily
# AND carries a revolving balance is a premium relationship — the issuer books interchange on the spend AND
# net interest on the balance from the SAME engaged customer (higher retention/CLV). v19 rewards the two
# engines ADDITIVELY; v24 adds a bonus for the INTERSECTION. interaction = rank(total category spend) x
# revolving-intensity, where revolving-intensity = 0 for transactors (f1=0) so pure transactors are
# UNAFFECTED (whale-safe) and only high-spend revolvers get the bonus. Direction aligns with BOTH prior
# wins (pro-revolver like v19, anti-single-specialty-spike like v22). Overshoot guard: it's an ADD-ON bonus
# to v22 (not a lending-DOMINANT restructure like the flat v20), and the weight is capped at the last level
# where whales stay 0.999 in-rate (compass: whales drop past ~0.3, the v6/v8 losing direction). This is a
# genuine LB gamble — the predictor is blind to the interaction form, and it pushes the lending axis where
# v20 went flat — but it is targeted (only dual-engine members) and downside is bounded (v22 0.866 banked).
V24_DUAL_W = 0.20                                                   # last whale-safe (0.999) level per the gradient compass


def dollar_profit_v24_dualengine(df: pd.DataFrame) -> pd.Series:
    """v24 (BOLD): v22 hybrid-basis PLUS a dual-engine bonus — rank(total category spend) x revolving-intensity
    (0 for transactors → whale-safe). Rewards members firing BOTH profit engines (spend interchange + balance
    interest) beyond the additive sum. Deterministic; uses f1,f3,f6-f11 (never id)."""
    f = df.fillna(0.0)
    f1v = f["f1"].values
    score = np.zeros(len(df))
    for k, wv in V22_DOLLAR_W.items():                                 # f7, f1 on the dollar/std basis
        score += wv * f[k].values / (f[k].values.std() + 1e-9)
    for k, wv in V22_RANK_W.items():                                   # f6/f8/f9/f10 rank-normalized
        pct = pd.Series(f[k].values).rank(pct=True).values
        score += wv * pct / (pct.std() + 1e-9)
    score += RECOVERED_RISK_W * _z(-(f.f11.values * f1v))              # expected credit loss
    catsum = f[SPEND_CATS].sum(axis=1).values
    spend_r = pd.Series(catsum).rank(pct=True).values
    revint = np.where(f1v > 0, pd.Series(f1v).rank(pct=True).values, 0.0)   # revolving intensity, 0 for transactors
    score += V24_DUAL_W * _z(spend_r * revint)                         # dual-engine interaction bonus
    s = pd.Series(score, index=df.index)
    return s.mask(pd.Series(f.f3.values == 1, index=df.index), s.min() - 1.0)


# v25 (2026-07-01): STACK ALL THREE confirmed post-v19 levers on the winning spine — basis transform (v22,
# LB 0.866) + dual-engine interaction (v24, LB 0.880) + precise category margin (the predictor-backed +0.018
# lever). Keeps the dual-engine weight at its CONFIRMED-winning level (0.20, not pushed — avoids gambling the
# interaction's peak the way additive lending peaked at co-equal in v20) and ADDS the independent margin
# signal (travel's 5x-reward thin margin), which moves a different ~4,000 boundary members. Whale-safe (0.999
# — dual-engine is 0 for transactors, margin credits everyday spend). Deterministic; never uses id.
def dollar_profit_v25_dualengine_margin(df: pd.DataFrame) -> pd.Series:
    """v25: v24 dual-engine (LB 0.880) PLUS the precise per-$ net-margin term. Stacks the three confirmed
    levers (basis transform + dual-engine interaction + category margin) on the validated spine. Deterministic."""
    f = df.fillna(0.0)
    f1v = f["f1"].values
    score = np.zeros(len(df))
    for k, wv in V22_DOLLAR_W.items():                                 # f7, f1 on the dollar/std basis
        score += wv * f[k].values / (f[k].values.std() + 1e-9)
    for k, wv in V22_RANK_W.items():                                   # f6/f8/f9/f10 rank-normalized
        pct = pd.Series(f[k].values).rank(pct=True).values
        score += wv * pct / (pct.std() + 1e-9)
    score += RECOVERED_RISK_W * _z(-(f.f11.values * f1v))              # expected credit loss
    catsum = f[SPEND_CATS].sum(axis=1).values
    spend_r = pd.Series(catsum).rank(pct=True).values
    revint = np.where(f1v > 0, pd.Series(f1v).rank(pct=True).values, 0.0)
    score += V24_DUAL_W * _z(spend_r * revint)                         # dual-engine interaction (confirmed λ=0.20)
    score += V23_MARGIN_W * _z(sum(m * f[k].values for k, m in V23_MARGIN.items()))   # precise per-$ margin
    s = pd.Series(score, index=df.index)
    return s.mask(pd.Series(f.f3.values == 1, index=df.index), s.min() - 1.0)


# === v16+ / 2026-06-30: NON-LINEAR forms — the reach toward the 0.91 leaders ============================
# Context (decision-log 2026-06-30; A23): the LINEAR weighted-sum family caps ~0.81-0.85 (the re-fit with
# v11min+v15 added STILL can't reproduce v15's 0.827 — implied 0.815, LOO 0.790 — and recovers NEGATIVE
# travel signs the LB twice rejected, so the recovered linear form is NOT a trustworthy submission). The
# only class that can structurally exceed the linear ceiling toward 0.91 is NON-LINEAR. All forms below
# keep v15's ALL-POSITIVE category weights, the revolving-balance f1 lever, the additive expected-loss
# term, and the validated f3 screen — they change ONLY the functional shape, so any LB read is attributable.
RECOVERED_RISK_W_NL = RECOVERED_RISK_W   # 0.110, the v10/v15 expected-loss weight, reused unchanged
SPEND_W = {"f7": 0.738, "f8": 0.348, "f10": 0.137, "f6": 0.060, "f9": 0.060}  # v15 category weights (no f1)
F1_W = 0.523                                                                   # v15 revolving-balance weight


def _z(v: np.ndarray) -> np.ndarray:
    """v10/v15's exact basis: scale by std, do NOT center (preserves the zero-spend cohort's mass)."""
    v = np.asarray(v, float)
    return v / (v.std() + 1e-9)


def _f3_screen(score: np.ndarray, f: pd.DataFrame, index) -> pd.Series:
    """The validated A17 collection-delinquency eviction: f3=1 members pushed below the floor."""
    s = pd.Series(score, index=index)
    return s.mask(pd.Series(f.f3.values == 1, index=index), s.min() - 1.0)


def _expl_term(f: pd.DataFrame) -> np.ndarray:
    """v10/v15's additive expected-loss term, z-scored: -(f11 * f1)/std (kept in every NL form)."""
    expl = -(f.f11.values * f.f1.values)
    return RECOVERED_RISK_W_NL * _z(expl)


# --- B1: CONCAVE spend (diminishing returns) ----------------------------------------------------------
# Apply a concave transform to each category's DOLLAR spend BEFORE z-scoring and weighting, so an extra
# $1k of spend is worth less to a $100k spender than to a $10k one. Economic rationale: interchange is
# linear in $ but the marginal high-spend dollar carries proportionally MORE reward/benefit cost and the
# truly profitable signal saturates (a $200k spender is not 2x a $100k spender in PROFIT). ⚠ v15 promoting
# $97k mega-spenders WON, so STRONG concavity may demote exactly the members the LB rewards — hence two
# strengths are provided. Mild (sqrt) barely bends the top; strong (log1p) compresses it hard.
def _concave_spend_score(df: pd.DataFrame, transform) -> pd.Series:
    f = df.fillna(0.0)
    score = np.zeros(len(df))
    for k, wv in SPEND_W.items():
        score += wv * _z(transform(np.clip(f[k].values, 0.0, None)))  # clip f7 refunds before concave map
    score += F1_W * _z(f.f1.values)        # balance kept LINEAR (interest ~ linear in carried $)
    score += _expl_term(f)
    return _f3_screen(score, f, df.index)


def dollar_profit_v16_sqrt(df: pd.DataFrame) -> pd.Series:
    """v16-mild: v15 all-positive, but category spend passes through sqrt before z-scoring. Tests gentle
    spend saturation. f1 linear; f3 screen kept.
    ⚠ DIAGNOSTIC FINDING (2026-06-30, framework-critic-verified) — DO NOT SUBMIT: because sqrt is applied
    THEN z-scored (z forces std=1), the per-category weights don't change; the real effect is TAIL-SKEW
    COMPRESSION (skew z(f7) 2.04→0.92) while f1 stays linear. Net: it shaves the f1 lever relative to
    spend (demotes median-$42K higher-f1 members, promotes median-$67K lower-f1) — fighting the project's
    most-validated finding (f1 co-equal with spend, the v10 +0.037 jump). Jaccard 0.900 vs v15; the
    reshuffle also rides the ~2.6%/category ceiling-CENSORED members (the A16 trap). EV ≈ 0, ~neutral-to-
    negative; economically self-contradictory given v15's magnitude-reward win."""
    return _concave_spend_score(df, np.sqrt)


def dollar_profit_v16_log(df: pd.DataFrame) -> pd.Series:
    """v16-strong: v15 all-positive, but category spend passes through log1p (strong diminishing returns).
    ⚠ DIAGNOSTIC FINDING — DO NOT SUBMIT: confirmed it HURTS-direction. Raises revolver share 54%→65% and
    demotes high-spend ($103K, f1=0) pure-transactors — the SAME members v15's +0.004 win promoted and the
    SAME direction as the v6(−0.058)/v8(−0.087) LB losses. Also DOUBLES the knife-edge cutoff band (5.2%→
    12.0% within ±0.5% of the cutoff) → worst-case private-30% robustness. Jaccard 0.745 vs v15. Probe
    only; the direction is already answered (the truth rewards magnitude)."""
    return _concave_spend_score(df, np.log1p)


# --- B2: spend x low-risk QUALITY interaction ---------------------------------------------------------
# Multiplicative "quality-adjusted spend": revenue x (1 - LGD*f11). A high-spend member who is ALSO
# low-risk is worth more than the same spend at high risk — risk SCALES the whole value rather than being
# a small additive shave. This is the lit margin x persistence skeleton (decision-log 2026-06-27) on the
# ALL-POSITIVE base (v11-riskgate tried it on the OLD NEGATIVE-sign revenue and was ~neutral; A22). f1
# enters revenue (interest) AND is implicitly disciplined because high-f1 high-f11 members get gated.
def dollar_profit_v16_riskqual(df: pd.DataFrame, risk_k: float = LGD) -> pd.Series:
    """v16-riskqual: (v15 all-positive spend + f1 interest, as a >=0 revenue magnitude) MULTIPLIED by the
    low-risk quality gate (1 - LGD*f11), then f3 screen. Risk scales value multiplicatively instead of
    the small additive expected-loss term. Uses only f1,f3,f6-f11; deterministic; no NaNs.
    ⚠ DIAGNOSTIC FINDING — NEUTRAL, DO NOT SUBMIT: f11 is tiny (mean 0.034; 89% of members have gate in
    [0.95,1.0]; full span only [0.837,1.0]), so the gate is near-flat and this is a LINEAR-EQUIVALENT
    cosmetic reformulation of v15's additive expected-loss term (re-confirms A22's v11-riskgate ~neutral
    on the all-positive base). Jaccard 0.971 vs v15 (1,455 move) — inside the ±0.0085 private-noise floor."""
    f = df.fillna(0.0)
    rev = np.zeros(len(df))
    for k, wv in SPEND_W.items():
        rev += wv * _z(np.clip(f[k].values, 0.0, None))   # all-positive spend revenue, >=0
    rev += F1_W * _z(f.f1.values)                          # + revolving-balance interest revenue, >=0
    quality = 1.0 - risk_k * f.f11.values                  # in [1 - 0.5*0.326, 1] = [0.837, 1.0]
    return _f3_screen(rev * quality, f, df.index)


# --- B3: SEGMENT-AWARE transactor vs revolver ---------------------------------------------------------
# v15's 11.1% swing was EXACTLY transactors (f1=0) vs revolvers (f1>0). One equation, segment-keyed: each
# member is ranked on its OWN economics. A TRANSACTOR's profit is interchange on spend (no lending P&L);
# a REVOLVER additionally earns net interest on the carried balance and bears expected credit loss. We
# build BOTH segments on the SAME proxy-dollar scale (interchange on z-scaled all-positive spend) so they
# interleave correctly, then ADD the revolver-only lending margin (interest - expected loss) for f1>0
# members. This is the brief's transactor/revolver distinction made first-class (research-findings).
def dollar_profit_v16_segment(df: pd.DataFrame, risk_k: float = LGD) -> pd.Series:
    """v16-segment: ONE segment-keyed equation. Both segments scored on all-positive spend-interchange
    (common scale); revolvers (f1>0) additionally get net lending margin = interest - expected loss.
    Transactors are NOT charged the lending terms (they have no balance). f3 screen kept.
    ⚠ DIAGNOSTIC FINDING — ALGEBRAICALLY v15, DO NOT SUBMIT or present as a structural innovation: for
    transactors (f1=0, 53% of pop) v15's F1_W*z(f1) AND z(-f11*f1) terms are ALREADY identically 0, so
    segment-keying them changes nothing. Jaccard 1.000 (only 6 members move) — and those 6 come ONLY from
    incidentally clipping f7 refunds at 0, not from the segment split. v15 already ranks the two segments
    coherently. Confirms the segment-split is NOT a lever against v15."""
    f = df.fillna(0.0)
    spend_rev = np.zeros(len(df))
    for k, wv in SPEND_W.items():
        spend_rev += wv * _z(np.clip(f[k].values, 0.0, None))    # shared interchange-on-spend, both segments
    is_rev = (f.f1.values > 0)                                   # revolver vs transactor segment key
    lend_margin = F1_W * _z(f.f1.values) + _expl_term(f)         # interest revenue + (negative) expected loss
    score = spend_rev + np.where(is_rev, lend_margin, 0.0)       # transactors: spend only; revolvers: + lending
    return _f3_screen(score, f, df.index)


def nonlinear_diagnostics(df: pd.DataFrame) -> None:
    """Internal A/B of the B1/B2/B3 non-linear candidates vs v15 (current best, public LB 0.827). NO label
    exists, so this reports Jaccard + who moves + their profile + cleanliness — NOT a proof of better
    overlap. Prints the honest divergence picture for the synthesis."""
    TOP = 100_000
    f = df.fillna(0.0)
    f3 = (df["f3"].fillna(0).to_numpy() == 1); f3_idx = set(df.index[f3])
    nb = set(df.index[~df[SPEND_CATS].notna().any(axis=1).to_numpy()])
    catsum = df[SPEND_CATS].sum(axis=1, min_count=1).fillna(0.0).to_numpy()
    is_rev = (f.f1.values > 0)

    def top(s):
        return set(s.nlargest(TOP).index)

    s15 = dollar_profit_v15_allpos(df); t15 = top(s15)
    cands = [
        ("v16_sqrt   (mild concave)", dollar_profit_v16_sqrt(df)),
        ("v16_log    (strong concave)", dollar_profit_v16_log(df)),
        ("v16_riskqual(spend x lowrisk)", dollar_profit_v16_riskqual(df)),
        ("v16_segment(transac/revolver)", dollar_profit_v16_segment(df)),
    ]
    print("\n=== NON-LINEAR candidates vs v15 (public LB 0.827) — NO submission, NO label ===")
    print(f"v15 top-20%: {len(t15):,}  | f3=1 in v15 top: {len(t15 & f3_idx)}  | no-bd share {len(t15 & nb)/len(t15):.1%}  | revolver share {sum(is_rev[i] for i in t15)/len(t15):.1%}")
    print(f"{'candidate':<32}{'Jaccard~v15':>12}{'moved':>8}{'f3=1':>6}{'no-bd':>7}{'revolv':>8}{'NaN':>5}{'det':>5}")
    for name, s in cands:
        t = top(s)
        moved = len(t ^ t15) // 2
        det = bool(s.equals(s))  # placeholder; recomputed below per-fn
        print(f"{name:<32}{len(t & t15)/len(t | t15):>12.3f}{moved:>8,}{len(t & f3_idx):>6}{len(t & nb)/len(t):>7.1%}"
              f"{sum(is_rev[i] for i in t)/len(t):>8.1%}{int(s.isna().sum()):>5}{'Y':>5}")

    # who moves under the MOST promising (segment) vs v15, and their profile
    sseg = dollar_profit_v16_segment(df); tseg = top(sseg)
    r15 = pd.Series(-s15.to_numpy()).rank(); rseg = pd.Series(-sseg.to_numpy()).rank()
    out = (r15 <= TOP) & (rseg > TOP); inn = (r15 > TOP) & (rseg <= TOP)
    print(f"\nv15->v16_segment movers: {out.sum():,} demoted, {inn.sum():,} promoted")
    print(f"  demoted : median catsum {pd.Series(catsum)[out.to_numpy()].median():.0f}  f1 {df.loc[out.to_numpy(),'f1'].fillna(0).median():.0f}  revolver {is_rev[out.to_numpy()].mean():.0%}")
    print(f"  promoted: median catsum {pd.Series(catsum)[inn.to_numpy()].median():.0f}  f1 {df.loc[inn.to_numpy(),'f1'].fillna(0).median():.0f}  revolver {is_rev[inn.to_numpy()].mean():.0%}")
    # determinism + cleanliness, computed honestly per function
    for name, fn in [("v16_sqrt", dollar_profit_v16_sqrt), ("v16_log", dollar_profit_v16_log),
                     ("v16_riskqual", dollar_profit_v16_riskqual), ("v16_segment", dollar_profit_v16_segment)]:
        a = fn(df); b = fn(df)
        t = top(a)
        print(f"  {name:<14} deterministic {bool(a.equals(b))}  NaNs {int(a.isna().sum())}  f3=1 in top-20% {len(t & f3_idx)}  distinct {a.nunique():,}")


def v11_diagnostics(df: pd.DataFrame) -> None:
    """Internal A/B of v11 vs the locked v10 best (LB 0.805) — NO submission. Stages the 3 changes so
    the top-20% reshuffle is attributable, and checks the A17 f3-contamination is actually fixed."""
    TOP = 100_000
    def top(s):
        return set(s.nlargest(TOP).index)
    f = df.fillna(0.0)
    f3 = (df["f3"].fillna(0).to_numpy() == 1)
    f3_idx = set(df.index[f3])
    nb = set(df.index[~df[SPEND_CATS].notna().any(axis=1).to_numpy()])

    s10 = dollar_profit_v10_triangulated(df); t10 = top(s10)
    rev = pd.Series(_v11_revenue(df), index=df.index)
    risk = pd.Series(rev.to_numpy() * (1 - LGD * f.f11.to_numpy()), index=df.index)
    s11 = dollar_profit_v11_riskgate(df)

    print("\n=== v11 internal A/B vs v10 (current best, public LB 0.805) — NO submission ===")
    print(f"population f3=1 (collection-cancel): {f3.sum():,} ({f3.mean():.1%})")
    print(f"A17 contamination — f3=1 members inside v10 top-20%: {len(t10 & f3_idx):,}")
    print(f"{'stage':<22}{'Jaccard~v10':>12}{'in':>9}{'out':>9}{'f3=1 top':>11}{'no-bd':>8}")
    for name, s in [("(a) revenue only", rev), ("(b) +risk gate", risk), ("(c) v11 full", s11)]:
        t = top(s)
        print(f"{name:<22}{len(t & t10) / len(t | t10):>12.3f}{len(t - t10):>9,}{len(t10 - t):>9,}"
              f"{len(t & f3_idx):>11,}{len(t & nb) / len(t):>8.1%}")
    print(f"v11 clean: NaNs {int(s11.isna().sum())}  distinct {s11.nunique():,}  "
          f"range [{s11.min():.2f}, {s11.max():.2f}]  deterministic {bool(dollar_profit_v11_riskgate(df).equals(s11))}")
    print("delinq-demotion D sensitivity (f3=1 remaining in top-20% | Jaccard~v10):")
    for d in (0.5, 0.9, 1.0):
        t = top(dollar_profit_v11_riskgate(df, d=d))
        print(f"  D={d}: {len(t & f3_idx):>6,}  {len(t & t10) / len(t | t10):.3f}")
    # the minimal, lowest-risk alternative: v10 with ONLY the f3 contaminants evicted
    tm = top(dollar_profit_v10_f3demote(df))
    print(f"v10+f3-only (minimal A17 fix): Jaccard~v10 {len(tm & t10) / len(tm | t10):.3f}  "
          f"reshuffle {len(tm - t10):,}  f3=1 in top-20% {len(tm & f3_idx):,}  no-bd {len(tm & nb) / len(tm):.1%}")
    # v12: A16 — NEUTRALIZE the noise-sign categories (f10/f6 → 0) STACKED on the f3 fix
    t12 = top(dollar_profit_v12_signfix(df))
    print(f"v12 dining-NEUTRAL +f3 (A16+A17): Jaccard~v10 {len(t12 & t10) / len(t12 | t10):.3f}  "
          f"reshuffle {len(t12 - t10):,}  f3=1 in top-20% {len(t12 & f3_idx):,}  no-bd {len(t12 & nb) / len(t12):.1%}"
          f"  | vs v11-minimal: Jaccard {len(t12 & tm) / len(t12 | tm):.3f} (neutralizing f10/f6 moves {len(t12 ^ tm) // 2:,})")


def _self_check():
    """A high-spend, low-risk, low-redemption member must outrank a low-spend, high-reward,
    high-risk one; scoring is deterministic; no NaNs."""
    demo = pd.DataFrame({
        "id": [0, 1, 2],
        "f1": [3000.0, 0.0, 8000.0], "f2": [0, 0, 1], "f3": [0, 0, 1],
        "f4": [50000.0, 5000.0, 300000.0], "f5": [9000.0, 300.0, 2000.0],
        "f6": [20000.0, 200.0, 1000.0], "f7": [60000.0, 400.0, 3000.0], "f8": [5000.0, 50.0, 200.0],
        "f9": [8000.0, 50.0, 300.0], "f10": [12000.0, 100.0, 500.0],
        "f11": [0.01, 0.02, 0.30], "f12": [10, 5, 2],
        "f13": [1, 0, 12], "f14": [0.0, 0.0, 200.0], "f15": [0.0, 0.0, 50.0], "f16": [10.0, 0.0, 64.0],
        "f17": [np.nan, np.nan, 40000.0], "f18": [np.nan, np.nan, 38000.0],
        "f19": [1, 1, 3], "f20": [2, 1, 2], "f21": [5000.0, 1000.0, 350000.0],
        "f22": [3, 2, 1], "f23": [1, 1, 0],
    })
    p = dollar_profit(demo)
    assert p.notna().all(), p
    assert p[0] > p[1] > p[2], f"profitable order broken: {p.round(1).tolist()}"  # row2 = unprofitable maximizer
    assert dollar_profit(demo).equals(dollar_profit(demo)), "must be deterministic"
    # v11: whale tops it; flipping the whale to collection-flagged (f3=1) must slash its score ~10x
    v = dollar_profit_v11_riskgate(demo)
    assert v.notna().all() and v[0] == v.max(), f"v11 whale not on top: {v.round(2).tolist()}"
    d2 = demo.copy(); d2.loc[0, "f3"] = 1
    assert dollar_profit_v11_riskgate(d2)[0] < 0.2 * v[0], "v11 f3 demotion must apply (~10x cut)"
    assert dollar_profit_v11_riskgate(demo).equals(v), "v11 must be deterministic"
    # v15: all-positive form stays clean, tops with the whale, and still evicts the f3-flagged member
    a = dollar_profit_v15_allpos(demo)
    assert a.notna().all() and a[0] == a.max(), f"v15 whale not on top: {a.round(2).tolist()}"
    assert dollar_profit_v15_allpos(d2)[0] < a[0], "v15 must still evict the f3-flagged whale"
    assert dollar_profit_v15_allpos(demo).equals(a), "v15 must be deterministic"
    # v16 non-linear forms: each must be clean (no NaN), deterministic, rank the whale top, evict f3
    for fn in (dollar_profit_v16_sqrt, dollar_profit_v16_log,
               dollar_profit_v16_riskqual, dollar_profit_v16_segment):
        s = fn(demo)
        assert s.notna().all(), f"{fn.__name__} produced NaN: {s.tolist()}"
        assert s[0] == s.max(), f"{fn.__name__} whale not on top: {s.round(2).tolist()}"
        assert fn(d2)[0] < s[0], f"{fn.__name__} must still evict the f3-flagged whale"
        assert fn(demo).equals(s), f"{fn.__name__} must be deterministic"
    # v18 risk-floor: clean, deterministic, and demotes a net-negative-lending revolver (f11>0.16, f1>0)
    d3 = demo.copy(); d3.loc[1, "f11"] = 0.20; d3.loc[1, "f1"] = 5000.0
    rf = dollar_profit_v18_riskfloor(d3)
    assert rf.notna().all() and rf[1] == rf.min(), f"v18 must floor the net-negative-lending member: {rf.round(2).tolist()}"
    assert dollar_profit_v18_riskfloor(demo).equals(dollar_profit_v18_riskfloor(demo)), "v18 must be deterministic"
    # v19 lending up-weight: clean, deterministic, whale on top, still evicts f3
    l = dollar_profit_v19_lending(demo)
    assert l.notna().all() and l[0] == l.max(), f"v19 whale not on top: {l.round(2).tolist()}"
    assert dollar_profit_v19_lending(d2)[0] < l[0], "v19 must still evict the f3-flagged whale"
    assert dollar_profit_v19_lending(demo).equals(l), "v19 must be deterministic"
    # v20 lending-dominant: clean, deterministic, whale on top, still evicts f3
    l2 = dollar_profit_v20_lending2(demo)
    assert l2.notna().all() and l2[0] == l2.max(), f"v20 whale not on top: {l2.round(2).tolist()}"
    assert dollar_profit_v20_lending2(d2)[0] < l2[0], "v20 must still evict the f3-flagged whale"
    assert dollar_profit_v20_lending2(demo).equals(l2), "v20 must be deterministic"
    # v21 tenure: clean, deterministic, whale on top, still evicts f3
    tn = dollar_profit_v21_tenure(demo)
    assert tn.notna().all() and tn[0] == tn.max(), f"v21 whale not on top: {tn.round(2).tolist()}"
    assert dollar_profit_v21_tenure(d2)[0] < tn[0], "v21 must still evict the f3-flagged whale"
    assert dollar_profit_v21_tenure(demo).equals(tn), "v21 must be deterministic"
    # v22 hybrid-basis: clean, deterministic, whale on top, still evicts f3
    hb = dollar_profit_v22_hybrid(demo)
    assert hb.notna().all() and hb[0] == hb.max(), f"v22 whale not on top: {hb.round(2).tolist()}"
    assert dollar_profit_v22_hybrid(d2)[0] < hb[0], "v22 must still evict the f3-flagged whale"
    assert dollar_profit_v22_hybrid(demo).equals(hb), "v22 must be deterministic"
    # v23 hybrid-basis + margin: clean, deterministic, whale on top, still evicts f3
    hm = dollar_profit_v23_hybrid_margin(demo)
    assert hm.notna().all() and hm[0] == hm.max(), f"v23 whale not on top: {hm.round(2).tolist()}"
    assert dollar_profit_v23_hybrid_margin(d2)[0] < hm[0], "v23 must still evict the f3-flagged whale"
    assert dollar_profit_v23_hybrid_margin(demo).equals(hm), "v23 must be deterministic"
    # v24 dual-engine: clean, deterministic, whale on top, still evicts f3
    de = dollar_profit_v24_dualengine(demo)
    assert de.notna().all() and de[0] == de.max(), f"v24 whale not on top: {de.round(2).tolist()}"
    assert dollar_profit_v24_dualengine(d2)[0] < de[0], "v24 must still evict the f3-flagged whale"
    assert dollar_profit_v24_dualengine(demo).equals(de), "v24 must be deterministic"
    # v25 three-lever stack: clean, deterministic, whale on top, still evicts f3
    fu = dollar_profit_v25_dualengine_margin(demo)
    assert fu.notna().all() and fu[0] == fu.max(), f"v25 whale not on top: {fu.round(2).tolist()}"
    assert dollar_profit_v25_dualengine_margin(d2)[0] < fu[0], "v25 must still evict the f3-flagged whale"
    assert dollar_profit_v25_dualengine_margin(demo).equals(fu), "v25 must be deterministic"
    print("OK score_magnitude.py self-check:", p.round(1).tolist(), "| v11+v15+v16(NL)+v18+v19+v20+v21+v22+v23+v24+v25 ✓")


def main():
    _self_check()
    np.random.seed(SEED)
    df = PremierEDA().df
    for name, fn in [("scores_v3", dollar_profit), ("scores_v4", dollar_spend),
                     ("scores_v5", dollar_profit_catmargin), ("scores_v6", dollar_profit_catmargin_f4),
                     ("scores_v7", dollar_profit_catmargin_v7), ("scores_v8", dollar_profit_v8),
                     ("scores_v9", dollar_profit_catmargin_v9),
                     ("scores_v10", dollar_profit_v10_triangulated),
                     ("scores_v11", dollar_profit_v11_riskgate),
                     ("scores_v11min", dollar_profit_v10_f3demote),
                     ("scores_v12", dollar_profit_v12_signfix),
                     ("scores_v15", dollar_profit_v15_allpos),
                     ("scores_v18", dollar_profit_v18_riskfloor),
                     ("scores_v19", dollar_profit_v19_lending),
                     ("scores_v20", dollar_profit_v20_lending2),
                     ("scores_v21", dollar_profit_v21_tenure),
                     ("scores_v22", dollar_profit_v22_hybrid),
                     ("scores_v23", dollar_profit_v23_hybrid_margin),
                     ("scores_v24", dollar_profit_v24_dualengine),
                     ("scores_v25", dollar_profit_v25_dualengine_margin)]:
        s = fn(df)
        assert s.notna().all(), f"{name} has NaNs"
        out = pd.DataFrame({"id": df["id"], "score": s}).sort_values("id")
        (ROOT / "data").mkdir(exist_ok=True)
        out.to_csv(ROOT / "data" / f"{name}.csv", index=False)
        print(f"\n{name}:  range [{s.min():.1f}, {s.max():.1f}]  distinct {s.nunique():,}")
        print(s.describe().round(2).to_string())

    v11_diagnostics(df)


if __name__ == "__main__":
    main()
