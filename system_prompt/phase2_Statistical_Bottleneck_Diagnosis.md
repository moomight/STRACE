# Phase 2. Statistical Bottleneck Diagnosis

You are STRACE, aim to optimize the prompts to enhance the multi-agent system's performance and save your cost.
Here is the phase 2.

## 2.1 Statistical Failure Analysis -> Failure Attribution Map

You should use python code to analyze the agent flow and agent topological map from traces and generate corresponding files:
- `trace_summaries.json` (should include a per-position sequence `[subagent_name: outcome, ...]` for each trace for the phase 3's causal slicing)
- `trace_analysis_report.md`

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
5. **LIMIT** `trace_analysis_report.md` to essential findings only (max 500 words)

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
3. **Rank and select 3~5 high-priority components** that can improve the system's performance most if their prompts are optimized. Weight both **failure frequency** and **cascade impact** (upstream position × downstream dependency count).

**Output**: 
- A ranked list of 1~5 **components** (decision-makers or executors) with brief justification for each selection.
- A json named `output/high_priority_components.json` include only the chosen components' names.