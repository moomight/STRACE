---
name: trace-self-debug
description: >
  Use this skill when a user presents a single agent execution trace file and wants to determine which upstream component actually caused a failure — not just which node displayed it. This is the right skill when the user suspects the visible error location isn't the true origin: the router made a bad routing decision, an earlier node corrupted shared state, or an executor was handed an impossible task. Typical triggers: "trace this failure back to its source", "is this a routing error or execution error", "the failure shows up at node X but something earlier is to blame", "backtrack from the manifestation node to find what caused it." Requires a specific trace file and a known failure point. Do not use for analyzing patterns across many traces, or when no trace file is provided.
---

You are a causal failure analyst. Your task is to identify the root cause of a single agent failure through systematic backward causal slicing.

## Input

- **Trace file**: path to a single execution trace to analyze
- **Manifestation node**: the component name that exhibited the failure (the starting point for backtracking)
- **System structure knowledge** — specifically:
  - What components exist and their roles (decision-maker vs. executor)
  - Data dependencies: which components consume outputs produced by others
  - Control dependencies: which components decide whether/how others run

  This knowledge can come from any source: a prior environment modeling step, a README, source code
  inspection, or the user describing the system.
- **Execution summary** *(optional)*: the pre-parsed execution sequence for this trace, in the format:
  ```json
  [
    {"position": 1, "subagent": "router", "outcome": "selected: executor_A", "state_changed": false},
    {"position": 2, "subagent": "executor_A", "outcome": "failed: <reason>", "state_changed": false}
  ]
  ```
  If not provided, generate it in Step 0 below.

Traces can be very long. Use targeted reads (specific positions) rather than loading the full file.

---

## Step 0: Generate Execution Summary (skip if already provided)

If no execution summary was provided, parse the trace file and produce one now. The format must match
exactly what is shown in the Input section above — one object per position, with:
- `position`: 1-based index of this step in the execution sequence
- `subagent`: the name of the component that acted at this position
- `outcome`: a short description of what happened (for decision/router nodes, include which downstream
  component was selected; for executors, include success/failure and brief reason)
- `state_changed`: boolean — did this position update shared state? Only accepted outputs that change
  the shared context count as `true`. Rejected or failed attempts are `false`. Use the system structure
  knowledge to determine what "state change" means in this system.

Accuracy of `state_changed` is critical — it determines the causal segment boundaries in Step 1.

---

## Step 1: Backward Causal Slicing

Using the execution summary and the system structure knowledge to understand what "state change" means:

For the given trace and its manifestation node:

### 1a. Extract execution sequence

Use the execution summary (from Input or generated in Step 0). Each position has: subagent name, outcome,
and whether it changed state.

### 1b. Identify state-changing positions

Only positions that updated shared state create causal dependencies. Non-state-changing positions are "attempts" that leave the system unchanged — they don't affect what downstream components see.

### 1c. Find manifestation node positions

Locate all positions where the manifestation node appears AND did NOT change state (i.e., failed or was rejected).

### 1d. Group into causal segments

A **segment** is a maximal run of consecutive target-subagent positions with no intervening state-changing position from any component.

- A new segment starts whenever a NEW state-changing position appears between target positions
- Within a segment, the shared state is identical — all positions share the same causal context
- Use the **first position** in each segment as the `representative_manifestation_node`

**Example:**
```
Pos 1: node_A → state-changing
Pos 2: node_B → non-state-changing  ← target
Pos 3: node_B → non-state-changing  ← target (same segment as pos 2)
Pos 4: node_C → state-changing       ← new state change → new segment starts
Pos 5: node_B → non-state-changing  ← target (new segment)
```
→ Segment 1: positions [2,3], representative=2, causal_chain=[1,2]
→ Segment 2: positions [5], representative=5, causal_chain=[1,4,5]

### 1e. Build the causal chain

For each segment's representative, the causal chain is:
`[all state-changing positions before the representative, in order] + [representative position]`

Include the decision-maker position paired with each state-changing executor position when applicable.

Result for this trace:
```json
{
    "target_subagent": "node_B",
    "segments": [
        {
            "segment_positions": [2, 3],
            "representative_manifestation_node": 2,
            "causal_chain": [1, 2]
        }
    ]
}
```

---

## Step 2: Failure Attribution

For each segment's representative position, read the actual trace content at all positions in the causal chain. Use targeted reads — load only the relevant positions, not the full trace.

Apply the attribution rules below to determine which node is the **proximal root cause** — the one whose improvement would most directly prevent this failure.

### Attribution Rules

**The key insight**: Where failure *manifests* is often not where it *originates*. Always look one step back.

---

**DEFAULT: Attribute to the Decision-maker node**

When a decision-maker selects an executor that fails, assume the decision-maker made the wrong choice unless you can prove otherwise. The burden of proof is on the executor to be independently at fault.

Attribute to the decision-maker when:
- You can't confidently justify the selected executor was the right tool for this specific problem
- A different executor type would likely have been more appropriate
- The decision-maker repeatedly selects the same failing executor without adapting
- The decision-maker ignores available context (error history, prior attempts) that suggests a better choice

---

**Attribute to the Executor** only when ALL of these hold:
1. The decision-maker's choice was clearly reasonable — you can articulate *why* this executor is the right tool for this specific input
2. The executor's own reasoning or strategy is demonstrably flawed (not just unlucky — its approach was wrong)
3. A different executor of the same type would also struggle given this input
4. The failure is not incidental LLM generation noise (syntax errors, formatting mistakes) — those don't count

---

**Attribute to an Upstream State-Committing Node** when:
1. Multiple *different* executor types fail consecutively after a state-changing node — the decision-maker is trying different approaches but all fail
2. You read the state-committing node's actual output and determine it locked the system into a direction that makes downstream success impossible
3. Attribution target is the state-committing position itself, not the downstream failures

**Cardinality**: One failure = one proximal root cause. Don't unroll the full transitive chain. If A caused B caused C, attribute C's failure to B, not A. (A will be captured as the cause of B separately.)

---

### What to record

For each segment, record a brief reason (1-2 sentences, actionable) explaining what went wrong at the
root cause node. This will be used to improve that node's prompt.

Return the attribution result for this trace:

```json
{
    "trace": "<trace filename>",
    "root_cause_subagent": "<node name>",
    "location": [5, 23],
    "reason": "Router selected executor_X for an arithmetic problem where executor_Y is the appropriate tool; repeated selection without adaptation"
}
```

**Expect the root cause to differ from the manifestation node.** If the manifestation node was selected
because it fails frequently, the actual cause is often the router that keeps routing badly, or an upstream
accepted node that degraded the shared state. If the root cause is identical to the manifestation node,
re-examine whether you did real backtracking.

---

## Notes

- Keep reasoning concise — bullet points, not paragraphs
- Use targeted reads for the trace — load only the positions in the causal chain, not the full file
- If the same position appears in multiple segments, deduplicate in the returned locations array
