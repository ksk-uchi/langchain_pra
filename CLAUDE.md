# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

LangChain practice repository (`langchain-pra`). Uses Python 3.14 managed via `mise` and `uv`.

## Commands

```bash
# Install dependencies
uv sync

# Run main entry point
uv run python main.py

# Run a specific script
uv run python <script.py>

# Add a dependency
uv add <package>
```

## Orders Workflow

This repo uses a structured **main agent / sub-agent** workflow under `Orders/`:

- **Main agent (planner/reviewer)**: Reads an `*.order.md` or `*.review.md` and produces process instruction files (`*.process_01.md`, `*.process_02.md`, ...) — does NOT write code directly.
- **Sub-agent (coder)**: Follows the process files to implement, test, and commit — one commit per phase.

### Creating a new Order

```bash
bash Orders/create_order.sh
```

This copies `Orders/00000_boilerplate/` into a new numbered directory (e.g., `Orders/00001_my-feature/`).

### Order directory structure

```
Orders/
  00000_boilerplate/      # Template — do not modify
    001.order.md          # Main agent: fill in background, requirements, constraints
    001.review.md         # Main agent: fill in review notes and Q items
  NNNNN_<name>/
    001.order.md          # Filled-in task spec
    001.process_01.md     # Sub-agent instructions, phase 1
    001.process_02.md     # Sub-agent instructions, phase 2 (if needed)
```

### Agent roles

**Main agent** (when given an `order.md` or `review.md`):
- Ask the user to clarify ambiguities before writing process files.
- Produce `*.process_*.md` with step-by-step instructions specific enough that the sub-agent needs no design decisions.
- Each phase ends with test execution and one commit.
- Do not edit code or commit directly.

**Sub-agent** (when given a `process_*.md`):
- Follow instructions exactly; do not refactor beyond the stated scope.
- Run tests and commit after each phase.
- UI/runtime verification is done by the user, not the agent.

### Review items (`review.md`) convention

- `[Q]` — question requiring user answer before work begins
- `[Q(Done)]` — answered question (kept as log, no action needed)
- `[Do]` — actionable instruction for the sub-agent
