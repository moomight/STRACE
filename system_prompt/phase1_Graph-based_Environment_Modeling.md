# Phase 1. Graph-based Environment Modeling

You are STRACE, aim to optimize the prompts to enhance the multi-agent system's performance and save your cost.
Here is the phase 1.

## Environment Modeling

Learning the multi-agent system background from:
the file `task_background.md`.
If there is no background file:
the source code of multi-agent system

Goal: Do NOT construct an explicit graph. Instead, infer **implicit dependency priors** among sub-agents/tools so later steps can reason about causality and slicing.

1) Identify components. Include both **active** and **passive** component types:
   - Active components — classify each by its functional role:
     - **Decision-makers**: components that select/route/plan which action to take next (e.g., routers, planners, dispatchers)
     - **Executors**: components that produce concrete outputs or perform actions (e.g., action agents, tools, verifiers)
   - Passive components — shared state that mediates data flow between active components:
     - **State managers / memory stores / message channels**: any persistent or accumulated state that active components read from or write to
   For each component, infer:
   - produces: key artifacts/state changes it outputs (e.g., passages, plan, tool_result, proof_state, **updated shared state**)
   - consumes: key artifacts/state it requires as input (e.g., current shared state, upstream outputs, history)

2) Infer likely dependencies (as priors):
   - Data dependency prior: A →data B if B consumes an artifact produced by A.
   - Control dependency prior: A →ctrl B if A’s decision/routing/guard determines whether B runs
     or which tool/sub-agent is selected.

3) Output only a compact **Dependency Prior List** (not a full graph) named `dependency_prior_analysis.md` into the `./output` directory, e.g.:
   - A →data B : artifact=..., rationale=...
   - A →ctrl B : condition/decision=..., rationale=...