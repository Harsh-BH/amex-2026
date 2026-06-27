# Standard — Documentation

- **The Framework writeup is a graded deliverable**, not an afterthought. Maintain it continuously in `.claude/templates/framework-doc.md` so the submission sheet is a copy-paste away.
- Every scoring component documents: *which feature(s)*, *why it's revenue/cost*, *the transformation*, *the weight and its rationale*. Tie back to `business-context.md`.
- Code docstrings explain **why**, not what — especially any business assumption baked into a number.
- Decisions → `memory/decision-log.md`. New facts/assumptions → `memory/assumptions.md`. Don't bury durable knowledge in code comments.
- Plots get a one-line caption stating the takeaway, not just the axes.
- Keep `CLAUDE.md` and `memory/` truthful and current — they are the project's source of truth for future sessions. Stale memory is worse than none.
