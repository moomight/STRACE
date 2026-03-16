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

### Option B: Skills + MCP Tools in Claude Code

Install the 4 skills and MCP tools into any project, then let Claude Code invoke them on demand.

**Setup:**

1. Copy (or symlink) `skills/` and `.mcp.json` into your target project:
   ```bash
   cp -r /path/to/STRACE/skills/ /your/project/skills/
   cp /path/to/STRACE/.mcp.json /your/project/.mcp.json
   cp /path/to/STRACE/tools_mcp.py /your/project/tools_mcp.py
   ```

2. Install the MCP dependency in your project's venv:
   ```bash
   pip install mcp
   ```

3. Adjust `.mcp.json` if your venv path differs:
   ```json
   {
     "mcpServers": {
       "strace-tools": {
         "command": ".venv/bin/python",
         "args": ["tools_mcp.py"]
       }
     }
   }
   ```

4. Open the project in Claude Code and give a task like:
   ```
   This is a multi-agent system. I need you to optimize the prompts based on
   the execution trajectories. The prompts are in <prompts_dir>/ and the
   traces are in traces/. Improve the success rate while keeping cost low.
   ```
   Claude Code will discover the skills and tools, then invoke them as needed.

**Skills provided:**

| Skill | What it does |
|-------|-------------|
| `agent-env-modeling` | Reads source code and docs to catalog all agents, prompts, and dependencies |
| `trace-selection` | Selects representative failing traces and computes execution summaries |
| `trace-self-debug` | Performs backward causal slicing on a single trace to attribute failure |
| `harness-engineering` | Generates prompt modification gradients from root-cause evidence |

**MCP Tools provided:**

| Tool | What it does |
|------|-------------|
| `search_context_in_file` | Search for text in files with configurable context window |
| `get_json_structure` | Show JSON file structure as a compact skeleton (type names + fingerprint grouping) |
| `read_trace_positions` | Read specific numbered positions from trace JSON files with smart truncation |

## Project Structure

```
STRACE/
├── run.py                 # Standalone entry point (Option A)
├── tools.py               # Tools for claude-agent-sdk (used by run.py)
├── tools_mcp.py           # Same tools as MCP server (used by Claude Code)
├── .mcp.json              # MCP server config for Claude Code
├── message_formatter.py   # Output formatting utilities
├── skills/                # Skill definitions (.skill bundles + SKILL.md sources)
│   ├── agent-env-modeling/
│   ├── trace-selection/
│   ├── trace-self-debug/
│   └── harness-engineering/
├── system_prompt/         # System prompts for each pipeline phase
├── prompts/               # Target prompts (example: VeruSAGE)
├── traces/                # Trace files go here (JSON)
└── output/                # Analysis outputs
```

## Requirements

- Python 3.10+
- `claude-agent-sdk` (for Option A)
- `mcp` (for Option B)

