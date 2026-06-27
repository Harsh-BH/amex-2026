"""LLM-as-judge convergent-validity check for the v1 score (OpenAI).

No profit label exists. This samples member PAIRS, asks an LLM which member is more profitable
to the issuer (given decoded feature profiles, with NO hint of our score), and measures how often
the LLM agrees with our ranking — and, for contrast, with the naive `f5` (total-spend) ranking.
A judge that agrees with us MORE than with naive spend is convergent-validity evidence; it is NOT
ground truth (the LLM has no more truth than we do). Use it to catch gross disagreements, not to
optimize toward.

Run:  .venv/bin/python src/llm_judge.py     # makes paid OpenAI API calls
"""
from __future__ import annotations
import os, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from eda import PremierEDA, FEATS, NAMES
from score import score, SEED

N = 240                  # member pairs to judge
MODEL = "gpt-4o-mini"    # cheap + capable enough for pairwise judgments
WORKERS = 8              # concurrent API calls

SYSTEM = (
    "You are a credit-card P&L analyst. Judge which cardmember is more profitable to the ISSUER "
    "(American Express) over a year. Issuer profit ~ revenue (card spend/interchange, interest on "
    "carried balances and lending lines, fees, extra cards) minus cost (rewards-points cost, "
    "lounge/airline/cab/entertainment credits, expected credit loss from default risk, and "
    "servicing/attrition). Decide on the economics, not engagement vanity metrics. Reply ONLY with JSON."
)


def load_env(path: str = ".env") -> None:
    """Load KEY=VALUE lines from repo-root .env into os.environ (stdlib; no python-dotenv)."""
    p = Path(__file__).resolve().parent.parent / path
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip().removeprefix("export ").strip()
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))


def profile_text(row: pd.Series) -> str:
    return "\n".join(f"- {NAMES[c]}: {'missing' if pd.isna(row[c]) else round(float(row[c]), 2)}"
                     for c in FEATS)


def user_prompt(a: pd.Series, b: pd.Series) -> str:
    return (f"Member A:\n{profile_text(a)}\n\nMember B:\n{profile_text(b)}\n\n"
            'Which member is more profitable to the issuer over a year? '
            'Reply strict JSON: {"more_profitable": "A" or "B", "reason": "<=20 words"}.')


def sample_pairs(df: pd.DataFrame, n: int, seed: int) -> list:
    """n distinct member pairs as presentation-ordered (A_idx, B_idx); A/B order randomized
    (seeded) to cancel any positional bias in the judge."""
    rng = np.random.default_rng(seed)
    idx = df.index.to_numpy()
    out, seen = [], set()
    while len(out) < n:
        a, b = (int(x) for x in rng.choice(idx, size=2, replace=False))
        key = (min(a, b), max(a, b))
        if key in seen:
            continue
        seen.add(key)
        if rng.random() < 0.5:
            a, b = b, a
        out.append((a, b))
    return out


def judge_pair(client, a_row: pd.Series, b_row: pd.Series, model: str):
    """One API call. Returns 'A' / 'B' / None (on any failure)."""
    try:
        r = client.chat.completions.create(
            model=model, temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": user_prompt(a_row, b_row)}],
        )
        ch = str(json.loads(r.choices[0].message.content).get("more_profitable", "")).strip().upper()
        return ch if ch in ("A", "B") else None
    except Exception:
        return None


def agreement(pairs: list) -> float:
    """Fraction of (llm_choice, ref_choice) that match, over non-None llm choices."""
    valid = [(l, r) for l, r in pairs if l is not None]
    return round(sum(l == r for l, r in valid) / len(valid), 3) if valid else float("nan")


def run(df: pd.DataFrame, n: int = N, model: str = MODEL, workers: int = WORKERS, seed: int = SEED) -> dict:
    from openai import OpenAI
    s = score(df)
    f5 = df.f5
    pairs = sample_pairs(df, n, seed)
    client = OpenAI()

    def one(pair):
        a, b = pair
        llm = judge_pair(client, df.loc[a], df.loc[b], model)
        ours = "A" if s[a] >= s[b] else "B"
        fa = f5[a] if pd.notna(f5[a]) else -1.0
        fb = f5[b] if pd.notna(f5[b]) else -1.0
        f5c = "A" if fa >= fb else "B"
        return llm, ours, f5c

    with ThreadPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(one, pairs))                       # list of (llm, ours, f5c)
    # on a CONTESTED pair (ours != f5) the LLM's pick matches exactly one of them — the real signal
    contested = [(llm, ours) for llm, ours, f5c in res if llm is not None and ours != f5c]
    return {
        "n_requested": n,
        "n_judged": sum(1 for r in res if r[0] is not None),
        "agreement_with_ours": agreement([(r[0], r[1]) for r in res]),
        "agreement_with_f5":   agreement([(r[0], r[2]) for r in res]),
        "n_contested": len(contested),
        "contested_sides_with_ours": agreement(contested),  # vs f5 = 1 - this
    }


def main():
    load_env()
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not found (.env not loaded?) — aborting.")
        return
    df = PremierEDA().df
    print(f"judging {N} sampled member pairs with {MODEL} ({WORKERS} workers; paid API calls)...\n")
    res = run(df)
    print(f"pairs judged:                  {res['n_judged']}/{res['n_requested']}")
    print(f"LLM agreement with OURS:       {res['agreement_with_ours']:.1%}")
    print(f"LLM agreement with f5:         {res['agreement_with_f5']:.1%}  (naive total-spend baseline)")
    print(f"\ncontested pairs (ours != f5):  {res['n_contested']}")
    print(f"  -> LLM sides with OURS:      {res['contested_sides_with_ours']:.1%}  (vs f5 = {1 - res['contested_sides_with_ours']:.1%})")
    print("\nread: contested >50% = on the cases where our framework and naive spend DISAGREE, the judge")
    print("      leans our way. ~50% = judge is indifferent. NOT ground truth — a cross-check only.")


if __name__ == "__main__":
    # pure-logic self-checks (no API)
    assert agreement([("A", "A"), ("B", "B"), ("A", "B"), (None, "A")]) == round(2 / 3, 3)
    sp = sample_pairs(pd.DataFrame(index=range(100)), 10, seed=1)
    assert len(sp) == 10 and all(a != b for a, b in sp)
    assert sample_pairs(pd.DataFrame(index=range(100)), 10, seed=1) == sp, "sampling must be reproducible"
    print("OK llm_judge self-checks pass\n")
    main()
