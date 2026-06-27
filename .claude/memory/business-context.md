# Business Context — Premier Card P&L

_How the issuer makes and loses money on a Premier cardmember. This is the economic spine of the framework._

## The product
Flagship ultra-premium **charge card**. Annual fee $500–750. Target: high-income frequent
travelers. "No preset spending limit," but revolving balance (`f1`) and lend lines
(`f17`,`f18`) exist → a Pay-Over-Time / Plan It lending component coexists with the charge card.

## Revenue to issuer
| Source | Driven by | Notes |
|---|---|---|
| Discount/interchange on spend | `f5`–`f10` | **Dominant lever.** Amex's spend-centric model. 5x categories (air/hotel) spend more but cost more rewards. |
| Net interest income | `f1` (revolve), `f17`/`f18` (lend lines) | Profitable *if* risk is contained. |
| Annual fee | (all members) | **Constant within product → does not differentiate.** Ignore for ranking. |
| Supplementary-card fees | `f19` | More supp accounts → more spend + fee. |

## Cost to issuer
| Cost | Driven by | Notes |
|---|---|---|
| Rewards cost | `f21` (redeemed), `f4` (outstanding balance/liability) | Earned points scale with spend, esp. 5x categories. |
| Benefit / lifestyle credits | `f13` lounge, `f14` airline credit, `f15` cab, `f16` entertainment credit | Real cash outflows; "free" perks the issuer pays for. |
| Expected credit loss | `f11` risk score, `f3` collection calls, revolve/lend exposure | High risk erodes interest gains. |
| Servicing / attrition | `f2` cancel calls, `f3` collection calls, maybe `f12` logins | Cost + churn risk. |

## Profit intuition (NOT the final equation — see framework skill)
`profit ≈ spend-margin + interest + supp-fees − rewards − benefit-credits − expected-loss − servicing`

## "Good" vs "bad" cardmember
- **Good:** high spend in profitable categories, profitably revolves/lends at low risk,
  multiple cards/supp, engaged (won't churn), benefit cost small *relative to* spend.
- **Bad:** low spend but heavy benefit/credit burn, high risk score, collection calls,
  wants to cancel — a net-negative premium holder.

## Why this matters for the model
The hidden ground truth is almost certainly a sensible revenue−cost computation (plausibly on
these same masked features). **The closer our economics mirror a real issuer P&L, the higher
the top-20% overlap.** This rewards business sense, not ML horsepower.
