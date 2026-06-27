# Checklist — Before Running an Experiment

- [ ] Written a **one-line hypothesis** (what change, expected effect, why — business reason).
- [ ] Started an experiment record from `templates/experiment.md`; assigned `exp-NNN`.
- [ ] Seed fixed; config captured; baseline to compare against identified.
- [ ] Change is **business-justifiable**, not a blind public-LB chase.
- [ ] Internal validation planned (top-20% stability on resamples), not just "submit and see".
- [ ] Confirmed this won't silently overfit the public 70% (would it survive on unseen rows?).
- [ ] Submission budget checked — is this worth one of the 10? (Validate internally first when possible.)
