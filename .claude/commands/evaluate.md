---
description: Validate the current score's top-20% stability before submitting.
argument-hint: [score version, e.g. "v3"]
---
Invoke the **evaluation** skill.

Target: $ARGUMENTS

**Expected output:** top-20% stability across resamples, sensitivity to weights, score-distribution sanity, plausibility spot-check of top members, and a keep/kill read on overfit risk.

**Internal workflow:** cutoff → 70/30 resample stability → weight sensitivity → distribution sanity → business plausibility → decision. Public LB is NOT ground truth.
