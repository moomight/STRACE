# STRACE: Trajectory Analysis and Causal Extraction for Long-Horizon Agent Optimization

A toolkit for analyzing multi-agent system execution traces, identifying root causes of failures, and generating prompt optimizations.

## Overview

STRACE provides a 4-phase analysis pipeline:

1. **Environment Modeling** — Catalog all components, prompts, and dependencies in a multi-agent system
2. **Trace Selection** — Sample representative failing traces and reduce token cost
3. **Causal Root-Cause Attribution** — Backward causal slicing on individual traces to locate failure sources
4. **Harness Engineering** — Generate concrete prompt modifications (gradients) based on root-cause evidence

## Two Ways to Use

### Option A: Standalone Script (`run.py`)

Run the full pipeline as a single Python process using `claude-agent-sdk`:

```bash
pip install claude-agent-sdk
mkdir -p traces && cp /path/to/your/traces/* traces/
python run.py
```

The script orchestrates all 4 phases sequentially, reads from `traces/`, and writes results to `output/`.

### Option B: Agent Skill `strace`

Install the `strace` skill into any project, then let your coding agent run the pipeline on demand.

**Setup:**

1. Copy the `strace` skill into your target project:
   ```bash
   cp -r /path/to/STRACE/skills/strace/ /your/project/<agent-skill-dir>/strace/
   ```

   For example, in Claude Code this is typically:
   ```bash
   cp -r /path/to/STRACE/skills/strace/ /your/project/.claude/skills/strace/
   ```
   In Copilot CLI this is:
   ```bash
   cp -r /path/to/STRACE/skills/strace/ /your/project/.github/skills/strace/
   ```

2. Open the project in your coding agent environment and give a task like:
   ```
   This is a multi-agent system. I need you to optimize the prompts based on
   the execution trajectories. The prompts are in <prompts_dir>/ and the
   trajectories are in traces/. Improve the success rate while keeping cost low.
   ```
   Your agent can discover the `strace` skill, triage the situation, and run the appropriate pipeline stages.

**Pipeline stages** (orchestrated by `skills/strace/SKILL.md`):

| Stage | Agent | What it does |
|-------|-------|-------------|
| 1 | `agent-env-modeling` | Catalog all components, prompts, and dependencies |
| 2 | `trace-selection` | Select representative failing traces, compute execution summaries |
| 3 | `trace-self-debug` | Backward causal slicing on individual traces to attribute failures |
| 4 | `harness-engineering` | Generate prompt modifications (gradients) from root-cause evidence |

The skill includes a **triage step** that decides which stages to skip based on existing outputs and context.

The skill includes helper scripts under `skills/strace/scripts/` for targeted trace inspection:

| Tool | What it does |
|------|-------------|
| `scripts/search_context_in_file.py` | Search for text in files with configurable context window |
| `scripts/get_json_structure.py` | Show JSON file structure as a compact skeleton (type names + fingerprint grouping) |
| `scripts/read_trace_positions.py` | Read specific numbered positions from trace JSON files with smart truncation |

## Project Structure

```
STRACE/
├── run.py                 # Standalone entry point (Option A)
├── utils.py               # Utility tools for claude-agent-sdk (used by run.py)
├── message_formatter.py   # Output formatting utilities
├── skills/
│   └── strace/            # Unified skill (Option B)
│       ├── SKILL.md       # Orchestrator with triage + pipeline
│       ├── agents/        # Stage-specific agent instructions
│       │   ├── agent-env-modeling.md
│       │   ├── trace-selection.md
│       │   ├── trace-self-debug.md
│       │   └── harness-engineering.md
│       └── scripts/       # Helper scripts for targeted trace inspection
│           ├── get_json_structure.py
│           ├── read_trace_positions.py
│           └── search_context_in_file.py
├── system_prompt/         # System prompts for each pipeline phase (Option A)
├── traces/                # Trace files go here (JSON)
└── output/                # Analysis outputs
```

## Requirements

- Python 3.10+
- `claude-agent-sdk` (for Option A)

