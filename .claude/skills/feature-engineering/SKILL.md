---
name: feature-engineering
description: Use when deriving transformations and composite features for the profitability score — scaling, ratios (margin proxies), risk adjustments. Invoke via /features during framework design. Only existing f1–f23 allowed.
---

# Feature Engineering

## Purpose
Shape `f1`–`f23` into terms the equation can combine fairly and that capture profit economics (margins, risk-adjusted revenue), using only existing variables.

## Inputs
EDA findings; `business-context.md`; `feature-notes.md`.

## Outputs
A set of transformed/derived features with documented rationale (→ `feature-doc.md`), feeding the scoring equation.

## Invocation Conditions
- During framework design, after EDA and missing-value rules are set.

## Workflow
1. **Scale:** normalize heavy-tailed features (log1p on spends/rewards) and put all terms on comparable ranges before weighting.
2. **Margin proxies:** ratios like benefit-cost / spend, rewards-redeemed / spend, revolve / lend-line — capture profitability better than raw magnitudes.
3. **Risk adjustment:** discount revenue terms by risk (`f11`) and collection signal (`f3`).
4. **Structural flags:** `has_lend_line`, `is_rewards_member` from missingness (per missing-value skill).
5. **Engagement:** combine `f12`/`f22` (and weak `f23`) into a light engagement signal if it helps the top tail.
6. Document each derived feature; add a runnable check it computes as intended.

## Best Practices
- Only `f1`–`f23` (+ flags derived from them). **No external data, no `id`.**
- Keep transforms interpretable — they must be explainable in the writeup.
- Prefer monotonic, sign-correct transforms (don't flip a cost into a reward).

## Common Mistakes
- Mixing raw scales (`f11`≈0.03 with `f4`≈126K) without normalization.
- Engineering opaque features that can't be justified (gaming-audit risk).
- Treating `f5` as the spend total (A1) when building ratios.

## Example Usage
"/features risk-adjusted spend." → `log1p(f5) * (1 - f11_scaled)` with a comment tying it to interchange revenue net of expected loss.
