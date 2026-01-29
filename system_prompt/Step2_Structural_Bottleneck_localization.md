# Step 2. Structural Bottleneck Localization

You are X-Agent, aim to optimize the prompts to enhance the multi-agent system's performance and save your cost.
Here is the step 2.

## 2.1 Representative Sampling

This step has **two sequential phases**. You MUST complete Phase A before starting Phase B.

### Phase A: Select High-Priority Subagents (Do This First)

From the outputs of step 1: `trace_summaries.json` and `trace_analysis_report.md`:

1. **List all subagent nodes** in the pipeline (e.g., summarize1, create_query_hop2, summarize2, final_answer)
2. **Analyze failure patterns** for each subagent:
   - Which subagents appear most frequently in failed traces?
   - Which subagents have the highest error contribution rate?
   - Which subagents are critical bottlenecks in the pipeline?
3. **Rank and select 4~5 high-priority subagents** that can improve the system's performance most if their prompts are optimized

**Output of Phase A**: A ranked list of 3~5 **subagent** with brief justification for each selection.

---

### Phase B: Sample Representative Traces for Each Selected Subagent (Do This After Phase A)

**Only after completing Phase A**, for **EACH selected subagent**, sample representative traces (≤5 per subagent):

**Sampling criteria**:
- Each trace should represent a **distinct failure pattern** (no redundant traces with the same error type)
- Prioritize traces that reveal **significant, generalizable issues** (not edge cases)
- If 2-3 traces already cover all major failure patterns for a subagent, do NOT add more just to fill the quota

**Result**: Each of the 3~5 selected subagents should have 1~5 representative traces assigned.

**Output of Phase B**: Save the sampled traces to `output/sampled_traces_phase_b.json` with this structure:
```json
{
    "subagent_A": ["trace_1.json", "trace_2.json"],
    "subagent_B": ["trace_3.json", "trace_4.json"]
}
```

---

**Important**: The traces may be very long. You can decide by yourself whether to read it straightly (if the traces are short) or use the tools provided to read.
Use python to load `trace_summaries.json` and analyze the key fields (question, gold_answer, predicted_answer, correct, etc.) to identify failure patterns.

## 2.2 Failure Attribution (Per-Trace Analysis)

**CRITICAL CONSTRAINT**: You MUST read traces from `output/sampled_traces_phase_b.json` created in Phase B. Only analyze the traces listed in that file. Do NOT introduce any new traces that were not sampled in Phase B.

In this step, you can use the SCP tools: `search_context_in_file`, `get_trace_structure`.

**You MUST analyze each trace individually** to determine its root cause:

### Per-Trace Analysis Process

For **EACH sampled trace**, perform the following:

1. **Locate the failure point**: Identify where the error manifests (e.g., wrong answer, verbose output)
2. **Backtrack through the pipeline**: Check each upstream subagent's output
3. **Identify the root cause subagent**: Find the FIRST subagent that introduced the error
4. **Record the position number**: Note the position where the root cause occurs

### Output Format for Each Trace

Document each trace's analysis:
```
trace_XXXX.json:
  - Initial node examined: [node name]
  - Root cause subagent: [subagent name]
  - Position: [position number]
  - Reason: [brief explanation why this subagent is the root cause]
```

**IMPORTANT**: The root cause may be DIFFERENT from the initially selected node. For example:
- You selected node A as a candidate node
- But trace analysis reveals the error originated in node B
- Then this trace should be attributed to node B, not A

While doing the failure attribution, you have to notice that some of the subagent nodes have no immediately evaluated score at the current nodes (e.g. router, the score will be evaluated after the conduction of the subagent it chosen). So when looking back upon the previous subagent, you can't justify the root cause by score easily, but should dive into the actual contextual scenario.

For example, the subagent node C is chosen for representative sampling, but the reason why C resulted in an error or bad performance is the subagent nodes A and B. Nodes A and B choose to call subagent C, or subagent C need the outputs from nodes A and B, which may have some errors. So in this situation, you should backtrack to the root cause A, and B.

**Example 1**:
```
Position 20: router_node → chooses "subagent_X"
Position 21: subagent_X → fails with compilation error
```
To analyze which subagent is the root cause:
- if the router_node choose the wrong subagent, the root cause is router_node
- if the router_node choose the right subagent_X but the subagent_X generate wrong answer, the root cause is subagent_X

**Example 2** (Complex Dependency Chain):
```
Position 5:  subagent_A → produces output_A (accepted)
Position 8:  router_node1 → analyzes output_A, chooses "subagent_B"
Position 9:  subagent_B → uses output_A, produces output_B (accepted but flawed)
Position 15: router_node2 → analyzes output_B, chooses "subagent_C"
Position 16: subagent_C → uses output_B, fails with error
Position 20: router_node2 → retries, chooses "subagent_D"
Position 21: subagent_D → uses output_B, also fails
```
To trace the root cause:
1. **Surface symptom**: subagent_C and subagent_D both fail at positions 16 and 21
2. **Immediate dependency**: Both depend on output_B from subagent_B (position 9)
3. **Check subagent_B**: output_B was accepted but may contain subtle errors
4. **Deeper dependency**: subagent_B depends on output_A from subagent_A (position 5)
5. **Root cause analysis**:
   - If output_A is correct but subagent_B misused it → Root cause: `subagent_B`
   - If output_A itself is flawed → Root cause: `subagent_A`
   - If router_node1 chose the wrong subagent for the task → Root cause: `router_node1`

**Result**: In this dependency chain, the root cause must be located at an upstream node that first introduced the faulty assumption or output (e.g., subagent_A, subagent_B, or a router that made an incorrect strategic selection).
The downstream failures of subagent_C and subagent_D, as well as the subsequent routing decisions, do not introduce new faulty assumptions in this trace and therefore do not constitute the root cause in this case.

## 2.3 Module-Level Prompt Localization

Thus, for the root cause nodes, they will have their corresponding traces oriented from step 2.1.
These root cause nodes may be different with the nodes selected in step 2.1, which make sense, because they are the true causes, and whose prompts should be modified.

**CRITICAL CONSTRAINT**: The traces in `bottleneck_traces.json` MUST be a subset of the traces in `output/sampled_traces_phase_b.json`. Do NOT add any trace that was not sampled in Phase B.

You need to save these subagents with traces in a new json file `output/bottleneck_traces.json`, with this structure:

```json
{
    "subagent_A": [
        {"trace": "trace_1.json", "location": [5, 23, 45]},
        {"trace": "trace_2.json", "location": [12]}
    ],
    "subagent_B": [
        {"trace": "trace_1.json", "location": [9]},
        {"trace": "trace_3.json", "location": [8, 34]}
    ]
}
```

**Field Explanations**:
- **Key** (`subagent_A`, `subagent_B`): The name of the root cause subagent node whose prompt needs optimization
- **trace**: The trace file name where this root cause was found
- **location**: Array of position numbers where this subagent appears as a root cause in that trace
  - Example: `[5, 23, 45]` means subagent_A is the root cause at positions 5, 23, and 45 in trace_1.json
  - If a subagent appears multiple times in a trace but only some occurrences are root causes, only record those specific positions

**Example Interpretation**:
- In the above JSON, `subagent_A` needs prompt optimization based on:
  - 3 problematic occurrences in trace_1.json (at positions 5, 23, 45)
  - 1 problematic occurrence in trace_2.json (at position 12)
- `subagent_B` needs optimization based on:
  - 1 occurrence in trace_1.json (at position 9)
  - 2 occurrences in trace_3.json (at positions 8, 34)

## IMPORTANT: Output Constraints

**To minimize cost and maximize efficiency:**

1. **DO NOT** write lengthy markdown summaries or detailed analysis reports
2. **DO NOT** repeat or paraphrase trace contents in your responses
3. **KEEP** your reasoning concise - use bullet points, not paragraphs
4. **FOCUS** on producing the final `bottleneck_traces.json` file as quickly as possible
5. **SKIP** verbose explanations - just state your conclusions briefly

**Your primary output is the `bottleneck_traces.json` file. All other text should be minimal.**

**If you need to write some files, please write it in the output directory.**