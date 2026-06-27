---
name: visualization
description: Use when producing plots for EDA, score diagnostics, or the R2/R3 deck — clear, captioned, takeaway-first figures. Invoke during EDA, evaluation, and documentation.
---

# Visualization

## Purpose
Communicate evidence clearly — distributions, relationships, score behavior, and top-tier composition — for analysis and for the presentation rounds.

## Inputs
Data / scores; the question the figure answers.

## Outputs
Saved figures (`reports/eda_*.png`) each with a one-line takeaway caption.

## Invocation Conditions
- During EDA, evaluation, and when building the R2/R3 deck.

## Workflow
1. State the question the plot answers.
2. Pick the right form: histogram/log-hist (skewed spends), boxplot by segment, correlation heatmap, score-distribution + top-20% cutoff line, term-contribution bars for top members.
3. Label axes/units; annotate the takeaway directly on the figure.
4. Save with a descriptive name; log the takeaway.

## Best Practices
- Log-scale heavy tails (`f4`,`f7`,`f21`). One message per figure.
- Show the **top-20% cutoff** explicitly when plotting scores.

## Common Mistakes
- Unlabeled axes / no caption / no takeaway.
- Linear scale on heavy-tailed money features hides everything.

## Example Usage
"Plot the score distribution." → histogram with vertical line at the 80th percentile, caption: "Clean separation at the top-20% cutoff; no tie pileup."
