# Terminology & Data Dictionary

_Decoded feature dictionary + domain glossary. The masked names map as below (source:
`docs/feature_description.xlsx`). Detailed stats/roles live in `feature-notes.md`._

## Feature dictionary
_Readable snake_case aliases per f-code live in `src/eda.py` `SHORT` — run `PremierEDA.legend()` to print code↔alias↔description. `f1`–`f23` stay canonical in code/memory/scoring._

| Code | Decoded name |
|---|---|
| `id` | Unique identifier (🚫 not a predictor) |
| `f1` | Average Revolve Balance in last 12m |
| `f2` | Cancellation Calls in last 12m |
| `f3` | Cancellation Calls due to Collection |
| `f4` | Rewards Points Balance |
| `f5` | Total Spend in last 12m |
| `f6` | Airlines Spend in 12m |
| `f7` | Other Spend in 12m |
| `f8` | Entertainment Spend in 12m |
| `f9` | Lodging Spend in 12m |
| `f10` | Dining Spend in 12m |
| `f11` | Average Risk Score in 12m |
| `f12` | Login Counts to website |
| `f13` | Lounge Access Count |
| `f14` | Credits used in airlines |
| `f15` | Cab benefits usage |
| `f16` | Entertainment Credit Used Amount |
| `f17` | Total Lend Line Amount |
| `f18` | Total Consumer Lend Line Amount |
| `f19` | Number of Supplementary Accounts |
| `f20` | Count of Active Charge Cards |
| `f21` | Rewards points redeemed in 12 months |
| `f22` | Emails Open in Last 6 months |
| `f23` | Emails Clicked in Last 6 months |

## Domain glossary
- **CM / Cardmember** — the customer holding the card.
- **Issuer** — American Express (who we estimate profit *for*).
- **Charge card** — settled in full each cycle (vs revolving credit). Premier is a charge card with an added Pay-Over-Time/lend component.
- **Revolve balance** — balance carried period-to-period, accruing interest (revenue + risk).
- **Lend line** — credit line available for the lending (Plan It / Pay Over Time) feature.
- **Interchange / discount revenue** — fee the issuer earns on cardmember spend; Amex's core revenue.
- **Rewards liability** — accounting cost of unredeemed points (`f4`); realized on redemption (`f21`).
- **Benefit credits** — lounge/airline/cab/entertainment/lifestyle perks the issuer pays for.
- **Risk score** — likelihood of default/loss (`f11`); higher = costlier.
- **Top-20%** — the 100K members the metric cares about; our score's top quintile is compared to the true top quintile.
- **Public/Private LB** — leaderboards on the 70%/30% random split.
