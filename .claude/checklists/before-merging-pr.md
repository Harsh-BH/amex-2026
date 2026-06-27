# Checklist — Before Merging a PR

- [ ] Branch is focused; one logical change.
- [ ] Code follows `standards/python.md`; lint/format clean.
- [ ] Runnable checks pass (`standards/testing.md`); scoring still deterministic.
- [ ] No `docs/` data, submissions, secrets, or large binaries committed (`.gitignore` honored).
- [ ] `memory/` updated if the change embodies a decision/assumption/experiment.
- [ ] PR body (from `templates/pull-request.md`) states what/why + any LB effect.
- [ ] Self-review or `/review` done; no `id` leakage introduced.
- [ ] `CLAUDE.md`/standards still accurate after the change.
