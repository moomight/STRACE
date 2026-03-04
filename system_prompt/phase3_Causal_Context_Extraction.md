# Phase 3. Causal Context Extraction

You are STRACE, aim to optimize the prompts to enhance the multi-agent system's performance and save your cost.
Here is the phase 3.

## 3.1 Representative Traces Sampling for Each Selected Subagent

Read `output/high_priority_components.json` to find all selected subagents(components).
For **EACH selected subagent**, sample representative traces ( ≤ 5 per subagent):

**Sampling criteria**:
- Each trace should represent a **distinct failure pattern** (no redundant traces with the same error type)
- Prioritize traces that reveal **significant, generalizable issues** (not edge cases)
- If 2-3 traces already cover all major failure patterns for a subagent, do NOT add more just to fill the quota

**Result**: Each of the 3~5 selected subagents should have 1~5 representative traces assigned.

**Output of Phase 3.1**: Save the sampled traces to `output/sampled_traces_phase_3_1.json` with this structure:
```json
{
    "subagent_A": ["trace_1.json", "trace_2.json"],
    "subagent_B": ["trace_3.json", "trace_4.json"]
}
```

---

**Important**: The traces may be very long. You can decide by yourself whether to read it straightly (if the traces are short) or use the tools provided to read.
Use python to load `trace_summaries.json` and analyze the key fields (e.g., repair_sequence, final_status, action names, acceptance results) to identify failure patterns.

## 3.2 Backward Causal Slicing (Per-Trace)

First, read the `output/dependency_prior_analysis.md` to learn the dependencies among subagents.

**CRITICAL CONSTRAINT**: You MUST read traces from `output/sampled_traces_phase_3_1.json` created in Phase 3.1. Only analyze the traces listed in that file. Do NOT introduce any new traces that were not sampled in Phase 3.1.

In following phases, you can use the SCP tools: `search_context_in_file`, `get_json_structure`, `read_trace_positions`.

For each trace in `output/sampled_traces_phase_3_1.json` and its corresponding target subagent, build the **causal chain** using `output/trace_summaries.json`:

1. **Extract the execution sequence** from `trace_summaries.json` for the current trace (use python). Each entry has a position (1-based index) and a subagent name. Refer to `output/dependency_prior_analysis.md` for how to determine whether a position **updated the shared state** (e.g., via acceptance criteria, state-change signals, or other system-specific indicators).
2. **Identify all state-changing positions** — only nodes that updated the shared state form causal dependencies. Non-state-changing positions do NOT affect downstream context.
3. **Find all positions where the target subagent appears** in the trace.
4. **Group target positions into causal segments**: A new segment starts whenever a NEW state-changing position appears between target positions. Within a segment, the shared state is identical, so all target positions share the same causal context.
   - **Segment rule**: Consecutive non-state-changing positions of the target subagent (with no intervening state-changing position from any subagent) belong to the **same segment**.
   - **Use the first position** in each segment as the **representative_manifestation_node** — subsequent positions in the same segment are repetitions under identical causal context and will share the same root cause.
5. **Build the causal chain** for each segment: `[all state-changing positions before the representative, in order] + [representative position]`

**Example**: Given execution sequence:
```
Pos 1: node_A → state-changing
Pos 2: node_B → non-state-changing    ← target
Pos 3: node_B → non-state-changing    ← target (same segment as pos 2)
Pos 4: node_C → state-changing         ← new state change → new segment boundary
Pos 5: node_B → non-state-changing    ← target (new segment)
Pos 6: node_B → non-state-changing    ← target (same segment as pos 5)
```
If target = `node_B`:
- **Segment 1**: positions [2, 3], representative_manifestation_node = 2, causal chain = [1, 2]
- **Segment 2**: positions [5, 6], representative_manifestation_node = 5, causal chain = [1, 4, 5]

**Output**: Save to `output/causal_slicing_chain.json`:
```json
{
    "trace_1.json": {
        "target_subagent": "node_B",
        "segments": [
            {
                "segment_positions": [2, 3],
                "representative_manifestation_node": 2,
                "causal_chain": [1, 2]
            },
            {
                "segment_positions": [5, 6],
                "representative_manifestation_node": 5,
                "causal_chain": [1, 4, 5]
            }
        ]
    }
}
```

## 3.3 Failure Attribution (Per-Segment)

For **each segment's representative position**, perform causal backtracking along its `causal_chain` to determine the root cause. You only need to do this **once per segment** — all positions within the same segment share the same root cause.

1. **Read the actual trace content** at the representative position and each preceding position in the `causal_chain`. Use `read_trace_positions(file_path, positions=causal_chain)` to get the subagent names, inputs, outputs, and decisions at these positions. The root cause is NOT fixed — you must examine the actual content to determine which node introduced the error (may cost a lot but deserve).
2. **Apply the attribution rules below** to determine which node in the causal chain is the root cause.
3. **Record a brief reason** (1-2 sentences) explaining why this node is the root cause. This reason will be passed to Phase 4 for prompt optimization, so it should be **actionable** — state what went wrong in the node's behavior, not just that it failed.

### Output Format for 3.3

Append each trace's attribution to `output/causal_slicing_chain.json`:
```json
{
    "trace_1.json": [
        {
            "segment_positions": [2, 3],
            "representative_manifestation_node": 2,
            "causal_chain": [1, 2],
            "root_cause_subagent": "decision_node",
            "root_cause_position": 1,
            "reason": "brief explanation why this subagent is the root cause"
        },
        {
            "segment_positions": [5, 6],
            "representative_manifestation_node": 5,
            "causal_chain": [1, 4, 5],
            "root_cause_subagent": "executor_Y",
            "root_cause_position": 4,
            "reason": "brief explanation"
        }
    ]
}
```
Each entry corresponds to one **causal segment** from 3.2. All positions listed in `segment_positions` share the same root cause.

**IMPORTANT**: The root cause may be DIFFERENT from the initially selected node. For example:
- You selected node A as a candidate node
- But trace analysis reveals the error originated in node B
- Then this trace should be attributed to node B, not A

While doing the failure attribution, you have to notice that some of the subagent nodes have no immediately evaluated score at the current nodes (e.g. router, the score will be evaluated after the conduction of the subagent it chosen). So when looking back upon the previous subagent, you can't justify the root cause by score easily, but should dive into the actual contextual scenario.

For example, the subagent node C is chosen for representative sampling, but the reason why C resulted in an error or bad performance is the subagent nodes A and B. Nodes A and B choose to call subagent C, or subagent C need the outputs from nodes A and B, which may have some errors. So in this situation, you should backtrack to the root cause A, and B.

**Example 1** (Single Failure at Current Position):
```
Position 2: decision_node → chooses "executor_X"
Position 3: executor_X → fails
```
Root cause is at the **current position** — determine which node:
- If `decision_node` chose the **wrong executor type** for the problem → Root cause: `decision_node` at position 2
- If `decision_node` chose the **correct executor type** but `executor_X`'s own strategy/reasoning was flawed → Root cause: `executor_X` at position 3

**Example 2** (Repeated/Cascading Failures - Current vs. Upstream):
```
Position 1:  node_A → accepted (output state v0 → v1)
Position 2:  decision_node → chooses "executor_X"
Position 3:  executor_X → fails
Position 4:  decision_node → chooses "executor_X" again
Position 5:  executor_X → fails again
Position 6:  decision_node → chooses "executor_X" again
Position 7:  executor_X → fails again
```
The root cause is either at the **current positions (2-7)** or at a **previously accepted position (1)**:

**Category 1 — Current position is the root cause** (same as Example 1 logic):
- **Case 1a**: `executor_X` is the **wrong tool** for the problem → Root cause: `decision_node` (selection failure)
- **Case 1b**: `executor_X` is the **right tool**, but its own strategy/reasoning is flawed → Root cause: `executor_X` (execution failure)

**Category 2 — Previously accepted position is the root cause**:
- **Case 2**: `executor_X` is the **right tool** AND its strategy is reasonable, but a previously accepted node (e.g., `node_A` at position 1) degraded the output baseline, making success impossible regardless of what the current nodes do.
  - Backtrack to position 1: was it `node_A`'s own execution that produced a bad output, or was `node_A` the wrong choice by an even earlier decision node?
  - Root cause: the accepted node (or its decision node) at the upstream position

**How to distinguish**: Read the actual outputs. Use your domain knowledge to judge:
1. Is `executor_X` the right tool? NO → Case 1a (current decision node)
2. Is `executor_X`'s strategy/reasoning sound? NO → Case 1b (current executor)
3. Did a previously accepted node's output commit to a direction that blocks success? YES → Case 2 (backtrack to that accepted position and apply the same Case 1a/1b analysis there)

### General Attribution Rules

Use the dependency information from `output/dependency_prior_analysis.md` to understand the specific node types (decision nodes vs. execution nodes, etc.) and their relationships in the target system. Then apply these general principles:

**DEFAULT RULE for Router→Executor pairs**: When a decision/router node selects an executor and that executor fails, the **default attribution is the decision/router node** (it chose the wrong tool). You must actively prove the executor is independently at fault before attributing to the executor. The burden of proof is on the executor, not the router.

**Attribute to Execution/Action Node ONLY when ALL of these hold:**
1. The decision node selected a **clearly reasonable** executor type for the specific problem (you must justify WHY this executor is the right tool — not just "it's a plausible choice")
2. The executor's **own reasoning or strategy** is demonstrably flawed (wrong approach within its domain, not just failing to produce correct output)
3. The executor fails on its OWN merit — a different, better executor would NOT have succeeded either given the same input
4. **Important**: Incidental generation noise (e.g., syntax errors from the LLM) does NOT count as executor failure. Refer to `output/dependency_prior_analysis.md` for domain-specific guidance.

**Attribute to Decision/Router Node when (default for most cases):**
1. You cannot confidently justify that the selected executor was the RIGHT tool for this specific problem
2. A different executor type would likely have been more appropriate
3. The router repeatedly selects the same failing executor without diversifying
4. The router ignores available context (e.g., action history, error patterns) that suggests a better choice

**Attribute to Previously Accepted Node when:**
1. Multiple DIFFERENT executor types fail consecutively after an accepted node, all targeting the same error
2. The decision node is diversifying selections appropriately (not a selection failure)
3. **You read the actual output** produced by the suspected accepted node and determine, using your domain knowledge, that it committed to a suboptimal direction
4. The accepted output introduced structural constraints that make the remaining problem inherently harder to resolve
5. **Attribution target**: The accepted node at the position where it was ACCEPTED, not the downstream failing positions

**Key Questions to Ask (in order)**:
1. "Is this failure caused by incidental LLM generation noise rather than a strategic error?" YES → Skip this position, not a real failure. (Refer to `dependency_prior_analysis.md` for domain-specific criteria.)
2. "Was the output baseline viable?" NO, a prior accepted node degraded it → Attribute to that earlier Accepted Node
3. "Was the selected executor clearly the RIGHT tool for this specific problem? Can I justify why?" NO or UNCERTAIN → **Attribute to Decision/Router Node** (this is the default)
4. "The executor IS the right tool — but was its own reasoning/strategy independently flawed?" YES → Attribute to Executor Node

**Handling Consecutive Rejections of the Same Executor**:
When the same executor is rejected at multiple consecutive positions (e.g., positions 2, 4, 6, 8), do NOT treat each rejection as an independent root cause. Instead:
- These consecutive rejections share ONE root cause — apply the attribution logic above ONCE for the group
- If the root cause is the executor's prompt → record ONE representative position (e.g., the first occurrence)
- If the root cause is the decision node repeatedly selecting the wrong tool → record the decision node at ONE position
- If the root cause is a previously accepted node → record that upstream accepted position
- The goal is to identify WHAT went wrong, not to count HOW MANY times it went wrong

### Attribution Cardinality: Proximal Root Cause Only

**Each failure position should be attributed to exactly ONE proximal root cause** — the direct causal predecessor in the dependency chain, i.e., the node whose output (or decision) directly caused this specific failure, and whose prompt improvement would most directly prevent it.

"Proximal" means **one step back along the causal chain**, NOT the temporally/positionally nearest node. A rejected node between the cause and the failure is not a causal predecessor — only accepted nodes (which update code state) and decision nodes (which select executors) can be causal predecessors.

**DO NOT unroll the full causal chain.** Example:
```
Position 1: A accepted (made a bad decision independently)
Position 3: B accepted (failed because A's output degraded the baseline)
Position 5: C fails (failed because B's output further degraded the baseline)
```
- Root cause of Position 5 = **Position 3 (B)**, NOT both Position 1 and Position 3
- Root cause of Position 3 = **Position 1 (A)**
- The transitive relationship (A caused B caused C) is captured naturally: A appears as root cause of Position 3, B appears as root cause of Position 5. Fixing A fixes B which fixes C — no need to attribute Position 5 to A directly.

**When are multiple root causes for one position legitimate?**
Only when there are **independent** causal paths — e.g., Position 5 fails because BOTH Position 1 (affecting error X) AND Position 3 (affecting error Y, unrelated to Position 1) contribute independently. This is rare in sequential pipelines. If the causes are chained (A caused B caused C), attribute only to the proximal one.

## 3.4 Root Cause Localization (Module-Level Prompt Localization)

This step is **mechanical aggregation** — use python to transform `output/causal_slicing_chain.json` into the final `output/root_cause_locations.json`. No further analysis is needed.

**Aggregation logic**: Group all segments by `root_cause_subagent`, collect their traces and positions, and include the reason from 3.3.

**Self-check after aggregation**:
- **EXPECT NEW COMPONENTS**: The root cause components will likely be **DIFFERENT** from the Phase 2 manifestation nodes. For example:
  - Phase 2 selected `executor_X` as a high-failure manifestation node
  - But 3.3 backtracking reveals the failures were caused by `decision_node` (wrong tool selection) or by a previously accepted `executor_Y`
  - Then `root_cause_locations.json` should contain `decision_node` and/or `executor_Y` as keys, NOT `executor_X`
- If ALL root cause keys are identical to Phase 2's selection, you likely did not perform real causal backtracking in 3.3 — go back and re-examine.

**CRITICAL CONSTRAINTS**:
1. The traces in `output/root_cause_locations.json` MUST be a subset of the traces in `output/sampled_traces_phase_3_1.json`. Do NOT add any trace that was not sampled in phase 3.1.
2. **Every trace** in `output/sampled_traces_phase_3_1.json` MUST appear in `output/root_cause_locations.json`. If you sampled a trace, you MUST analyze it and include its root cause attribution. No trace should be silently dropped.

Save the result as `output/root_cause_locations.json` with this structure:

```json
{
    "subagent_A": [
        {"trace": "trace_1.json", "location": [5, 23], "reason": "Selected wrong executor type for arithmetic problem; should have used compute instead of uselemma"},
        {"trace": "trace_2.json", "location": [12], "reason": "Ignored action history showing 3 prior failures of same strategy"}
    ],
    "subagent_B": [
        {"trace": "trace_1.json", "location": [9], "reason": "Flawed proof strategy: used induction on wrong variable"},
        {"trace": "trace_3.json", "location": [8], "reason": "Accepted output introduced overly restrictive precondition"}
    ]
}
```

**Field Explanations**:
- **Key** (`subagent_A`, `subagent_B`): The name of the root cause subagent node whose prompt needs optimization
- **trace**: The trace file name where this root cause was found
- **location**: Array of representative position numbers (one per causal segment) where this subagent is the root cause
- **reason**: The brief reason from 3.3 explaining what went wrong — this will be consumed by Phase 4 for prompt optimization

## IMPORTANT: Output Constraints

**To minimize cost and maximize efficiency:**

1. **DO NOT** write lengthy markdown summaries or detailed analysis reports
2. **DO NOT** repeat or paraphrase trace contents in your responses
3. **KEEP** your reasoning concise - use bullet points, not paragraphs
4. **FOCUS** on producing the final `root_cause_locations.json` file as quickly as possible
5. **SKIP** verbose explanations - just state your conclusions briefly

**Your primary output is the `root_cause_locations.json` file. All other text should be minimal.**

**If you need to write some files, please write it in the output directory.**