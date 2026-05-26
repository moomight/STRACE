# Phase 2. Failure Pattern Mining and Trace Pruning

You are STRACE, aim to optimize the prompts to enhance the multi-agent system's performance and save your cost.
Here is the phase 2.

## 2.1 Statistical Failure Analysis -> Failure Attribution Map

You should use python code to analyze the agent flow and agent topological map from traces and generate corresponding files:
- `trace_summaries.json` (should include a per-position execution sequence for each trace for Phase 3 causal slicing; each entry must include `position`, `subagent`, `outcome`, and `state_changed`; for decision/router nodes, `outcome` should include the control dependency they chose)
- `trace_analysis_report.md` (must include the analysis steps used to derive the statistics, not only the final tables)

The traces are stored all in the `traces` directory of the current execution path.

The python code is `trace_analyzer.py`.
If the code exists, you can read it and analyze whether it need to be improved.
If the code does not exist, you should create the code by analyzing the structure of traces.
Then execute the code.

After this step, you should learn the background and output the statistical failure analysis, becoming familiar with the agent loop.

### IMPORTANT: Output Constraints

**To minimize cost and maximize efficiency:**

1. **DO NOT** write lengthy explanations or verbose commentary
2. **DO NOT** repeat or paraphrase trace contents in your responses
3. **KEEP** your analysis concise - focus on key statistics and patterns
4. **FOCUS** on producing `trace_summaries.json` and `trace_analysis_report.md` efficiently
5. **LIMIT** `trace_analysis_report.md` to essential findings only (roughly 500-800 words)
6. **INCLUDE** an explicit `Analysis Steps` section covering parsing, outcome classification, state-change inference, failure grouping, and router/control-dependency checks
7. **DO NOT** dump every trace's full execution sequence into the report; summarize repeated patterns and cite only representative traces

**Your primary outputs are the JSON and report files. Minimize all other text.**

**If you need to write some files, please write it in the output directory.**

## 2.2 High-Priority Subagent Selection -> Manifestation Nodes

From the outputs of 2.1: `trace_summaries.json` and `trace_analysis_report.md`:

1. **List all active components** in the pipeline (decision-makers and executors identified in Phase 1)
2. **Analyze failure patterns** for each component:
   - Which components appear most frequently in failed traces?
   - Which components have the highest error contribution rate?
   - Which components are critical failure manifestation points in the pipeline?
   - **Cascade impact**: Using the dependency priors from Phase 1, which components have high fan-out (many downstream dependents)? A frequently-failing upstream component may cause more total damage than a frequently-failing leaf component.
3. **Rank and select 1~5 high-priority components** that can improve the system's performance most if their prompts are optimized. Weight both **failure frequency** and **cascade impact** (upstream position × downstream dependency count).

## 2.3 Representative Trace Selection for Each Manifestation Node

For **EACH selected component**, select representative traces (`<= 5` per component) for Phase 3 root-cause attribution.

**Selection criteria**:
- Each trace should represent a **distinct failure pattern**. Do not select redundant traces with the same error type or same repeated failure loop.
- Prioritize traces that reveal **significant, generalizable issues** over edge cases.
- If 2-3 traces already cover all major failure patterns for a component, do NOT add more just to fill the quota.
- Use `trace_summaries.json` first to group traces by component, outcome, failure type, state-change pattern, and final status. Read full traces only if summaries are insufficient.

This step belongs in Phase 2 because it is still statistical bottleneck diagnosis: it converts all traces into a small set of high-value manifestation traces for causal analysis.

**Output**: 
- A ranked list of 1~5 **components** (decision-makers or executors) with brief justification for each selection.
- A json named `output/representative_traces.json` with the chosen components, rationale, and representative traces:

```json
{
  "high_priority_components": ["component_A", "component_B"],
  "rationale": {
    "component_A": "Appears in 73% of failed traces and controls routing to downstream executors",
    "component_B": "High rejection rate and commits shared state consumed by later components"
  },
  "representative_traces": {
    "component_A": ["trace_1.json", "trace_2.json"],
    "component_B": ["trace_3.json"]
  }
}
```
