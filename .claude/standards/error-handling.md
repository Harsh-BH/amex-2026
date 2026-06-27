# Standard — Error Handling

- **Fail loud at trust boundaries.** Data load and submission write must validate, not silently coerce.
- On load: assert expected columns (`id`,`f1`–`f23`), expected row count (500,000), and numeric dtypes. Raise with a clear message if not.
- **Never silently fill or drop.** Missing values are handled by an explicit, documented rule; an *unexpected* missing (e.g. in `f1`/`f2`/`f3` which should have none) raises.
- The submission writer **must refuse** to emit a file that: has ≠500K rows, has any null `Prediction`, is missing/duplicating `id`s, or used `id` as a feature. These are the disqualifying mistakes — guard them hard.
- Catch and report the broken-`pandas` import explicitly with the stdlib-fallback hint, rather than a cryptic AttributeError.
- Prefer specific exceptions with actionable messages over bare `except`. Don't swallow errors to "keep going" on a scoring run.
