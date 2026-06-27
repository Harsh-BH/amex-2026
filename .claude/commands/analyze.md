---
description: Restore project context and analyze the current state / a given question.
argument-hint: [optional question or focus area]
---
Invoke the **project-understanding** skill first (read `CLAUDE.md` + `.claude/memory/`), then the **data-understanding** skill if data is involved.

Focus: $ARGUMENTS

**Expected output:** a grounded summary of where the project stands (roadmap stage, decisions, open assumptions) and a direct answer to the focus, citing memory. No code unless asked.

**Internal workflow:** project-understanding → (data-understanding if relevant) → answer + flag any constraint risk (§16).
