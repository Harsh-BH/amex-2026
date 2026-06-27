# Standard — Configuration Management

- **All scoring knobs in one place.** Weights, normalization choices, missing-value rules, and the seed live in a single `config.py` (or `config.yaml`) — never scattered as literals across the code.
- Each config value carries a comment tying it to its business rationale and the experiment that set it.
- A submission run = code (pinned) + config (recorded). The experiment entry references the exact config so the result is reproducible.
- No secrets needed (no PII, no API). If any appear later, use env vars / `.env` (git-ignored), never commit them.
- Config changes are experiments — bump the version, log the hypothesis, don't quietly tweak a weight between submissions.
- Defaults must be safe: if a config field is missing, fail loudly rather than assume.
