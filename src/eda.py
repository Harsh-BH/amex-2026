"""Premier-card EDA toolkit — import the class into a notebook and call methods.

    from eda import PremierEDA, add_features
    eda = PremierEDA()          # loads (pickle-cached after first read)
    eda.overview()              # -> DataFrame; same for missingness/correlations/segments/top_tail
    eda.plot_distributions(); eda.plot_corr(); eda.plot_missingness()
    feats = add_features(eda.df)

Numeric methods return DataFrames (render in the notebook); plot_* methods draw.
Grounded in .claude/memory/{feature-notes,research-findings}. No `id` is ever used as signal.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "docs" / "6a3cb6104933b_campus_challenge_r1_data.xlsx"
CACHE = Path(__file__).resolve().parent.parent / "data" / "premier.pkl"
FEATS = [f"f{i}" for i in range(1, 24)]
NAMES = {  # from .claude/memory/terminology.md
    "f1": "Avg Revolve Balance 12m", "f2": "Cancellation Calls 12m", "f3": "Collection Cancel Calls",
    "f4": "Rewards Points Balance", "f5": "Total Spend 12m", "f6": "Airlines Spend", "f7": "Other Spend (refunds<0)",
    "f8": "Entertainment Spend", "f9": "Lodging Spend", "f10": "Dining Spend", "f11": "Avg Risk Score (PD-like)",
    "f12": "Website Logins", "f13": "Lounge Access Count", "f14": "Airline Credits Used", "f15": "Cab Benefit Months",
    "f16": "Entertainment Credit Used", "f17": "Total Lend Line", "f18": "Consumer Lend Line",
    "f19": "# Supplementary Accts", "f20": "# Active Charge Cards", "f21": "Rewards Redeemed 12m",
    "f22": "Emails Opened 6m", "f23": "Emails Clicked 6m",
}
SHORT = {  # readable snake_case alias per feature (display only; f-codes stay canonical)
    "f1": "revolve_bal", "f2": "cancel_calls", "f3": "collect_calls", "f4": "rewards_bal",
    "f5": "total_spend", "f6": "air_spend", "f7": "other_spend", "f8": "ent_spend",
    "f9": "lodge_spend", "f10": "dine_spend", "f11": "risk_score", "f12": "logins",
    "f13": "lounge_visits", "f14": "air_credit", "f15": "cab_months", "f16": "ent_credit",
    "f17": "lend_line", "f18": "consumer_lend", "f19": "supp_accts", "f20": "active_cards",
    "f21": "rewards_redeemed", "f22": "email_open", "f23": "email_click",
}
SPEND_CATS = ["f6", "f7", "f8", "f9", "f10"]
HEAVY_TAILED = ["f1", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f17", "f18", "f21"]


class PremierEDA:
    def __init__(self, path: Path = DATA, cache: Path = CACHE):
        if cache.exists():
            self.df = pd.read_pickle(cache)
        else:
            self.df = pd.read_excel(path, sheet_name=0)
            cache.parent.mkdir(exist_ok=True)
            self.df.to_pickle(cache)  # ponytail: pickle cache, not pyarrow; ~28s read -> instant reloads
        assert self.df.shape == (500000, 24), self.df.shape

    @staticmethod
    def legend() -> pd.DataFrame:
        """The f-code -> readable-name -> description map (run this first to learn the columns)."""
        return pd.DataFrame({"code": FEATS, "variable": [SHORT[c] for c in FEATS],
                             "description": [NAMES[c] for c in FEATS]}).set_index("code")

    def renamed(self) -> pd.DataFrame:
        """A copy of the data with readable column names (f5 -> total_spend). For free exploration."""
        return self.df.rename(columns=SHORT)

    # --- numeric summaries (return DataFrames, indexed by readable name) ---
    def overview(self) -> pd.DataFrame:
        d = self.df[FEATS]
        out = pd.DataFrame({
            "code": FEATS, "name": [NAMES[c] for c in FEATS],
            "missing%": (d.isna().mean() * 100).round(1).values,
            "min": d.min().round(2).values, "max": d.max().round(2).values,
            "mean": d.mean().round(2).values, "median": d.median().round(2).values,
            "skew": d.skew().round(2).values,
            "nonzero%": (((d != 0) & d.notna()).sum() / d.notna().sum() * 100).round(1).values,
        }, index=[SHORT[c] for c in FEATS])
        out.index.name = "variable"
        return out

    def missingness(self) -> pd.DataFrame:
        """Cluster features by which rows they co-miss (corr of missing-indicators)."""
        miss = self.df[FEATS].isna()
        cols = [c for c in FEATS if miss[c].any()]
        corr = miss[cols].astype(int).corr()
        # greedy cluster: features whose missingness corr >= 0.99 move together
        seen, clusters = set(), []
        for c in cols:
            if c in seen:
                continue
            grp = [k for k in cols if corr.loc[c, k] >= 0.99]
            clusters.append(grp); seen.update(grp)
        return pd.DataFrame({
            "cluster": [", ".join(g) for g in clusters],
            "missing%": [round(miss[g[0]].mean() * 100, 1) for g in clusters],
            "interpretation": [f"{', '.join(NAMES[x] for x in g[:3])}{'…' if len(g) > 3 else ''}" for g in clusters],
        }).sort_values("missing%", ascending=False).reset_index(drop=True)

    def correlations(self, thresh: float = 0.6, method: str = "spearman") -> pd.DataFrame:
        """Strong pairwise correlations (|r|>=thresh) — Spearman by default (honest for heavy tails)."""
        corr = self.df[FEATS].corr(method=method)
        pairs = [(a, b, round(corr.loc[a, b], 2))
                 for i, a in enumerate(FEATS) for b in FEATS[i + 1:]
                 if abs(corr.loc[a, b]) >= thresh]
        return (pd.DataFrame(pairs, columns=["a", "b", "r"])
                .assign(var_a=lambda x: x.a.map(SHORT), var_b=lambda x: x.b.map(SHORT))
                [["var_a", "var_b", "a", "b", "r"]]
                .sort_values("r", key=abs, ascending=False).reset_index(drop=True))

    def corr_order(self, method: str = "spearman") -> pd.DataFrame:
        """Rank features by overall correlation strength, strongest to weakest."""
        corr = self.df[FEATS].corr(method=method).abs()
        strength = (corr.sum() - 1) / (len(FEATS) - 1)
        order = strength.sort_values(ascending=False)
        strongest_partner = {}
        strongest_r = {}
        for c in order.index:
            peers = corr.loc[c].drop(c)
            top = peers.idxmax()
            strongest_partner[c] = SHORT[top]
            strongest_r[c] = round(self.df[[c, top]].corr(method=method).iloc[0, 1], 2)
        return pd.DataFrame({
            "code": order.index,
            "variable": [SHORT[c] for c in order.index],
            "corr_strength": order.round(3).values,
            "strongest_partner": [strongest_partner[c] for c in order.index],
            "strongest_r": [strongest_r[c] for c in order.index],
        }).reset_index(drop=True)

    def segments(self) -> pd.DataFrame:
        """Behavioral archetypes by mean profile (transactor/revolver/lender; rewards population)."""
        g = self.df.groupby(self._segment())
        out = pd.DataFrame({
            "n": g.size(), "share%": (g.size() / len(self.df) * 100).round(1),
            "total_spend": g.f5.mean().round(0), "revolve_bal": g.f1.mean().round(0),
            "risk_score": g.f11.mean().round(4), "rewards_bal": g.f4.mean().round(0),
            "cancel_calls": g.f2.mean().round(3),
        })
        return out.sort_values("share%", ascending=False)

    def top_tail(self, by: str = "f5", q: float = 0.8) -> pd.DataFrame:
        """What distinguishes the top (1-q) by `by` vs the rest — the metric only scores the top 20%.

        `by` accepts an f-code ("f5") or a readable name ("total_spend").
        """
        by = {v: k for k, v in SHORT.items()}.get(by, by)  # readable name -> f-code
        df = self.df
        cut = df[by].quantile(q)
        top, rest = df[df[by] >= cut], df[df[by] < cut]
        rows = {}
        for c in FEATS:
            rows[c] = [c, round(top[c].mean(), 2), round(rest[c].mean(), 2),
                       round(top[c].mean() / rest[c].mean(), 2) if rest[c].mean() else np.nan]
        out = pd.DataFrame.from_dict(rows, orient="index",
                                     columns=["code", f"top20%_by_{SHORT[by]}", "rest", "ratio"])
        out.index = [SHORT[c] for c in FEATS]; out.index.name = "variable"
        return out

    def _segment(self) -> pd.Series:
        """transactor (charge-only) / revolver (no lend line) / lender — from f1 (revolve) & f17 (lend line)."""
        df = self.df
        seg = pd.Series("transactor (charge-only)", index=df.index)
        seg[df.f17.notna()] = "lender (has lend line)"
        seg[(df.f1 > 0) & df.f17.isna()] = "revolver (no lend line)"
        return seg

    @staticmethod
    def _gini(x) -> float:
        x = np.sort(np.asarray(x, float)); x = x[~np.isnan(x)]
        if len(x) == 0:
            return float("nan")
        x = x - min(x.min(), 0.0)                       # shift to non-negative
        n, tot = len(x), x.sum()
        return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * tot)) if tot else float("nan")

    def weights(self) -> pd.DataFrame:
        """Objective, label-free feature weights on rank-normalized features (research §H).
        CRITIC = std × Σ_k(1−|corr_jk|): high when a feature is both variable AND non-redundant —
        deflates the collinear spend/lend clusters. Entropy & equal shown for comparison."""
        R = self.df[FEATS].rank(pct=True).fillna(0.5)   # rank-normalize; neutral fill for matrix math
        std = R.std()
        crit = std * ((1 - R.corr().abs()).sum())       # Σ_k (1 − |r_jk|)
        p = R / R.sum()
        ent = 1 - (-(p * np.log(p + 1e-12)).sum() / np.log(len(R)))   # 1 − normalized Shannon entropy
        out = pd.DataFrame({
            "variable": [SHORT[c] for c in FEATS], "std": std.round(3).values,
            "critic_w": (crit / crit.sum()).round(4).values,
            "entropy_w": (ent / ent.sum()).round(4).values,
            "equal_w": round(1 / len(FEATS), 4),
        }, index=FEATS)
        out.index.name = "code"
        return out.sort_values("critic_w", ascending=False)

    def concentration(self, cols=None) -> pd.DataFrame:
        """Gini per feature — how concentrated value is (1 = one member holds all). The metric only
        scores the top 20%, so high-Gini revenue features separate that tail best."""
        cols = cols or HEAVY_TAILED
        return pd.DataFrame({"variable": [SHORT[c] for c in cols],
                             "gini": [round(self._gini(self.df[c]), 3) for c in cols]},
                            index=cols).sort_values("gini", ascending=False)

    # --- plots (for the notebook) ---
    def plot_distributions(self, cols=None):
        import matplotlib.pyplot as plt
        cols = cols or HEAVY_TAILED
        n = len(cols); ncol = 4; nrow = -(-n // ncol)
        fig, ax = plt.subplots(nrow, ncol, figsize=(4 * ncol, 3 * nrow)); ax = np.array(ax).ravel()
        for i, c in enumerate(cols):
            s = self.df[c].dropna()
            ax[i].hist(np.log1p(s.clip(lower=0)) if (s >= 0).all() else s, bins=60)
            ax[i].set_title(NAMES[c] + ("  (log1p)" if (s >= 0).all() else ""), fontsize=8)
        for j in range(n, len(ax)):
            ax[j].axis("off")
        fig.tight_layout(); return fig

    def plot_corr(self, method: str = "spearman"):
        import matplotlib.pyplot as plt
        corr = self.df[FEATS].corr(method=method)
        order = (corr.abs().sum() - 1).sort_values(ascending=False).index.tolist()
        corr = corr.loc[order, order]
        fig, ax = plt.subplots(figsize=(9, 8))
        im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
        labels = [SHORT[c] for c in order]
        ax.set_xticks(range(len(order))); ax.set_xticklabels(labels, rotation=90, fontsize=7)
        ax.set_yticks(range(len(order))); ax.set_yticklabels(labels, fontsize=7)
        fig.colorbar(im, fraction=0.046); ax.set_title(f"Feature correlation ({method})"); fig.tight_layout(); return fig

    def plot_missingness(self):
        import matplotlib.pyplot as plt
        m = (self.df[FEATS].isna().mean() * 100).sort_values()
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.barh([SHORT[c] for c in m.index], m.values); ax.set_xlabel("% missing"); ax.set_title("Missingness by feature")
        fig.tight_layout(); return fig

    def plot_segment_profiles(self):
        """Heatmap: mean percentile-rank of each feature within each segment (archetype fingerprint)."""
        import matplotlib.pyplot as plt
        prof = self.df[FEATS].rank(pct=True).groupby(self._segment()).mean()
        fig, ax = plt.subplots(figsize=(11, 3.5))
        im = ax.imshow(prof.values, cmap="RdYlGn", vmin=0.35, vmax=0.65, aspect="auto")
        ax.set_xticks(range(len(FEATS))); ax.set_xticklabels([SHORT[c] for c in FEATS], rotation=90, fontsize=7)
        ax.set_yticks(range(len(prof.index))); ax.set_yticklabels(prof.index, fontsize=8)
        fig.colorbar(im, fraction=0.02, label="mean rank"); ax.set_title("Segment fingerprints (mean percentile-rank per feature)")
        fig.tight_layout(); return fig

    def plot_lorenz(self, cols=("f5", "f7", "f1", "f4")):
        """Lorenz curves — how concentrated each value pool is (more bowed = a few members hold most)."""
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.plot([0, 1], [0, 1], "k--", lw=1, label="equality")
        for c in cols:
            x = np.sort(self.df[c].dropna().clip(lower=0).to_numpy(float))
            if x.sum() == 0:
                continue
            cum = np.insert(np.cumsum(x) / x.sum(), 0, 0)
            ax.plot(np.linspace(0, 1, len(cum)), cum, label=f"{SHORT[c]} (G={self._gini(self.df[c]):.2f})")
        ax.set_xlabel("cumulative share of members"); ax.set_ylabel("cumulative share of value")
        ax.set_title("Lorenz curves — value concentration"); ax.legend(fontsize=8)
        fig.tight_layout(); return fig

    def plot_top_tail(self, by="f5"):
        """Diverging bars: top-20% mean ÷ rest mean per feature — what defines the high-value tail."""
        import matplotlib.pyplot as plt
        r = self.top_tail(by)["ratio"].sort_values()
        fig, ax = plt.subplots(figsize=(7, 6))
        ax.barh(r.index, r.values, color=["#c0392b" if v < 1 else "#27ae60" for v in r.values])
        ax.axvline(1, color="k", lw=1)
        ax.set_xlabel(f"top-20%-by-{SHORT.get(by, by)} mean ÷ rest mean"); ax.set_title("What defines the top 20%")
        fig.tight_layout(); return fig


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive interpretable features from f1–f23 only (no id). Grounded in research-findings.

    Returns a copy with new columns. Each is one line + business rationale.
    """
    d = df.copy()
    s = d[SPEND_CATS].sum(axis=1, min_count=1)               # total categorized spend (skips all-missing)
    # --- missingness-as-signal flags (MIA: encode, don't impute) ---
    d["has_lend_line"] = d.f17.notna().astype(int)            # ~charge-only when 0 (segment split)
    d["is_rewards_member"] = d.f4.notna().astype(int)         # rewards population
    d["has_spend_breakdown"] = d.f6.notna().astype(int)       # category detail present
    # --- segment ---
    d["is_revolver"] = ((d.f1 > 0) | d.f17.notna()).astype(int)
    # --- margin / efficiency ratios (research: margin-weight, don't sum raw) ---
    d["redemption_intensity"] = d.f21 / (d.f4 + d.f21)        # [0,1]; low => breakage => cheaper cost
    d["benefit_burden"] = (d[["f13", "f14", "f15", "f16"]].sum(axis=1, min_count=1)) / (d.f5 + 1)
    d["spend_diversity"] = (d[SPEND_CATS] > 0).sum(axis=1)    # # categories used (breadth ~ share-of-wallet)
    d["engagement"] = d.f12 / (d.f20 + 1)                     # logins per active card
    d["revolve_to_lend"] = d.f1 / d.f17                       # line utilization (NaN for charge-only)
    d["net_spend"] = s                                        # f7 refunds already netted in the sum
    # --- rank transforms of heavy tails (research: rank-normalize before combining) ---
    for c in HEAVY_TAILED:
        d[f"{c}_rank"] = d[c].rank(pct=True)                  # percentile in [0,1], NaNs stay NaN
    return d


if __name__ == "__main__":  # smallest runnable check
    eda = PremierEDA()
    assert eda.overview().shape[0] == 23
    f = add_features(eda.df)
    new = [c for c in f.columns if c not in eda.df.columns]
    assert len(new) == 10 + len(HEAVY_TAILED), new
    assert f["redemption_intensity"].between(0, 1).all(skipna := True) or f["redemption_intensity"].dropna().between(0, 1).all()
    print(f"OK: {len(new)} new features ->", new)
