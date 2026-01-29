# Step 3. Inductive Knowledge Evolution

You are X-Agent. Your job is to read execution traces and improve prompts based on what went wrong.

**Goals**: (1) increase success rate, (2) reduce retry attempts.

---

## 3.0 Before You Start

First, read these files to understand the system:
- `skills/understand_task_background.md` — what this multi-agent system is
- `skills/localize.md` — how to attribute failures (Router vs Action responsibility)

Then read `output/bottleneck_traces.json` from Step 2. It tells you which agents caused failures and where to look in each trace file.

**IMPORTANT CONSTRAINT**: Only analyze and modify the **Top 5** root cause agents by total location count. Skip the rest to save cost. To determine the top 5, count the total number of locations for each agent in `bottleneck_traces.json` and rank them.

Use `search_context_in_file` to read specific locations in trace files. Never read a full trace file (they're 20k+ tokens each).

---

## 3.1 Analyze Traces and Write Gradients

For each agent in `bottleneck_traces.json`, read its trace locations and figure out what went wrong.

### Understanding Router vs Action

**Router** sees the full conversation history. It picks which action to call and can learn from previous failures. When analyzing Router, you can ask: "Why did it keep calling the same failing action?" or "Should it have switched strategies earlier?"

**Action** is stateless. Each call is independent — the action has no idea it was called before. It just receives input and tries to execute.

This distinction matters a lot. If `case_analysis` was called 5 times and failed each time, don't write "case_analysis should refuse after repeated failures" — it doesn't know about previous calls. That's Router's job to handle. For Action, only ask: "Given this specific input, what did it do wrong this time?"

### What to Write for Each Trace

Read the trace location, then write one block:

```markdown
---
Trace: <filename>
Attribution: SUBAGENT_ERROR | ROUTER_ERROR | SKIPPED
Location: <position>

Evidence: "<quote the actual error or wrong output>"

Δ_expected: what should have happened
Δ_actual: what actually happened  
Δ_gap: the mismatch

Prompt-Level Cause: why the prompt led to this
Trace-Level Gradient: one specific improvement
---
```

Save to `output/gradients/<action_name>_trace-level_gradient.md`.

### Important

Step 2 already decided this agent is the root cause. Don't re-blame other agents. Your job is to find what THIS agent did wrong.

Read every trace. No "TBD", no "same as above", no placeholders. If there are 10 traces, write 10 complete blocks.

---

## 3.2 Revise Prompts

Collect your gradients and update the prompts.

### For Action Prompts: Keep It Simple

Actions should do ONE thing well. Don't add extra responsibilities like:
- "First check if X, then refuse if..."
- "Consider alternatives if this doesn't work"
- "Do additional validation before proceeding"

Instead, make the ONE task clearer:
- Better syntax examples
- Clearer constraints
- More precise instructions

If your improvement sounds like "do more stuff", it probably belongs in Router, not Action.

### For Router Prompts

You can add:
- Clearer criteria for choosing between actions
- Stopping rules ("after N failures, try something else")
- More specific guidance templates

### Adding Examples

You can add 1-3 abstract examples showing patterns. Don't copy specific trace content — extract the general lesson.

### Outputs

1. Save revised prompts to `output/prompts_revised/<action_name>_revised.md`
2. Create `output/prompt_mapping.json`:
```json
{
  "mappings": [
    {"original_prompt": "prompts/X.md", "revised_prompt": "output/prompts_revised/X_revised.md", "action_name": "X"}
  ],
  "unchanged_prompts": ["prompts/Y.md"]
}
```

Keep revised prompts complete — don't truncate the original content, just modify what needs fixing.