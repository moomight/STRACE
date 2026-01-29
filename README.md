# STRACE: Trajectory Analysis and Causal Extraction for Long-Horizon Agent Optimization

A multi-step agent system that analyzes agent execution traces to identify bottlenecks and optimize multi-agent system performance.

## Overview

STRACE uses a 4-step analysis pipeline on agent execution traces:

1. **Automated Diagnostic Profiling** - Graph-based Environment Modeling + Statistical Bottleneck Diagnosis
2. **Structural Bottleneck Localization** - Causal Context Extraction
3. **Inductive Knowledge Evolution** - Inductive Policy Evolution
4. (**Scope Boundary Validation** - Validating the scope of identified issues)

## Project Structure

```
STRACE/
├── run.py                 # Main entry point
├── tools.py               # Custom MCP tools for trace analysis
├── message_formatter.py   # Output formatting utilities
├── system_prompt/         # System prompts for each analysis step
│   ├── Step1_Automated_Diagnostic_Profiling.md
│   ├── Step2_Structural_Bottleneck_localization.md
│   ├── Step3_Inductive_Knowledge_Evolution.md
│   └── Step4_Scope_Boundary_Validation.md
├── skills/                # Background knowledge documents
├── traces/                # [Required] Your trace files go here
└── output/                # Analysis outputs will be saved here
```

## Prerequisites

- Python 3.10+

## Installation

```bash
# Install dependencies
pip install claude-agent-sdk
```

## Usage

### 1. Prepare Your Trace Data

Place your training set trace files in the `traces/` directory:

```bash
# Create the traces directory
mkdir -p traces

# Copy your trace files
cp /path/to/your/training_set/* traces/
```

> **Note**: The trace files should be JSON format containing agent execution logs.

### 2. Run the Analysis

```bash
cd STRACE
python run.py
```

### 3. Tool Permission

During execution, the system will prompt for tool usage confirmation:

```
Accept the tool usage? (y/n):
```

Some tools (like `search_context_in_file`) are auto-accepted. For other tools, type `y` to accept or `n` to deny.

## Custom Tools

The system provides several MCP tools for trace analysis:

| Tool | Description |
|------|-------------|
| `search_context_in_file` | Search for patterns in trace files with context window |
| `get_trace_structure` | Get the structure of a trace file |
| `read_multiple_line_ranges` | Read specific line ranges from files |

## Configuration

You can modify the permission mode in `run.py`:

```python
permission_mode="default",  # Options: "default", "acceptEdits", "plan", "bypassPermissions"
```

## Output

Analysis results are saved in the `output/` directory:

- `trace_summaries.json` - Structured summary of all traces
- `trace_analysis_report.md` - Human-readable analysis report
- Additional files generated during the analysis

