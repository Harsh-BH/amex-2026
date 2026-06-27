# Checklist — Before Writing Code

- [ ] Read `CLAUDE.md` §16 constraints and the relevant `memory/` files for this task.
- [ ] Is the code even needed? (Ponytail rung 1 — can a one-liner or existing script do it?)
- [ ] Confirmed the env works (`pandas`/`openpyxl` import, or using the stdlib xlsx fallback).
- [ ] Know which feature(s) this touches and their meaning/role (`feature-notes.md`).
- [ ] Decided where it lives (`src/` vs notebook) per `standards/folder-structure.md`.
- [ ] Not using `id` as a feature. Not altering `docs/` data.
- [ ] Have a named config home for any new knob (`standards/configuration.md`).
- [ ] Know what runnable check will prove it works (`standards/testing.md`).
