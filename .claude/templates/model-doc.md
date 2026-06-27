# Model / Scoring Doc — <name/version>

_For this problem the "model" is the profitability framework. Use this when a component grows
beyond the framework-doc summary (e.g. a learned calibration)._

- **Type:** interpretable equation / weighted score / (other — justify in decision-log)
- **Inputs:** features + transforms
- **Output:** continuous profitability score per `id`
- **Parameters / weights:** table of weight → component → rationale
- **How fit/calibrated:** business reasoning + any data-driven step (+ seed/config)
- **Assumptions baked in:** <list>
- **Validation:** top-20% stability, sensitivity analysis, overfit guard
- **Known limitations:** <list>
- **Reproduce:** command + commit/tag + config version
