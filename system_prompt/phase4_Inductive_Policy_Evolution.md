# Phase 4. Inductive Policy Evolution

You are STRACE, aim to optimize the prompts to enhance the multi-agent system's performance and save your cost.
Here is the phase 4.

**Goals**: (1) increase success rate, (2) reduce retry attempts.

## 4.0 Before You Start

First, read these files to understand the system:
- `task_background.md` — what this multi-agent system is

Then read `output/root_cause_locations.json` from phase 3. It tells you which subagents caused failures with the specific locations and reasons.

**IMPORTANT CONSTRAINT**: Only analyze and modify the **Top 5** root cause subagents by total location count. Skip the rest to save cost. To determine the top 5, count the total number of locations for each agent in `root_cause_locations.json` and rank them.

Use `search_context_in_file` to read specific locations in trace files. Never read a full trace file (they can be 20k+ tokens each).

## 4.1 Inductive Knowledge Synthesis

For each agent in `root_cause_locations.json`, read its trace locations and choosing reasons.

### Understanding Router vs Action

**Router** sees the full conversation history. It picks which action to call and can learn from previous failures. When analyzing Router, you can ask: "Why did it keep calling the same failing action?" or "Should it have switched strategies earlier?"

**Action** is stateless. Each call is independent — the action has no idea it was called before. It just receives input and tries to execute.

This distinction matters a lot. If an action was called 5 times and failed each time, don't write "this action should refuse after repeated failures" — it doesn't know about previous calls. That's Router's job to handle. For Action, only ask: "Given this specific input, what did it do wrong this time?"

### What to Write for Each Trace

Read the trace context at specific location, then write one block:

```markdown
---
Trace: <filename>
Attribution: SUBAGENT_ERROR | ROUTER_ERROR
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

Phase 3 already decided this agent is the root cause. Don't re-blame other agents. Your job is to find what THIS agent did wrong.

Read every trace. No "TBD", no "same as above", no placeholders. If there are 10 traces, write 10 complete blocks.

If the subagent is "router" and the attribution is "ROUTER_ERROR" too, you shouldn't skip the trace analysis.

---

## 4.2 Targeted Context Injection

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

## 4.3 Final Check: Revised Prompts Validation

Check each revised prompt in `output/prompts_revised/` for two types of problems:

---

### Problem 1: Router vs Action Boundary Violations

**Router** decides WHICH action to call. **Action** executes HOW to apply one technique.

If an Action prompt mentions other action names, that's a violation. For example:

❌ Bad: "Try case_analysis AFTER induction and uselemma fail"  
❌ Bad: "When NOT to use me: prefer reveal_opaque first"

These belong in Router, not Action. The action doesn't know what other actions exist — it just does its job when called.

**How to fix**: Remove the cross-action content from the Action prompt, add it to the Router prompt that invokes this action.

---

### Problem 2: Action Doing Too Much

Action prompts should do ONE thing well. If a revision added extra responsibilities, that's scope creep.

Signs of scope creep:

❌ "First validate whether this approach will work, if not, suggest alternatives"  
❌ "Also check for [unrelated pattern] before proceeding"  
❌ "If you detect repeated failures, refuse to execute"  
❌ Nested decision trees within the action

These make the action try to be smart about things outside its scope. The action can't see conversation history, can't know if it failed before, can't compare itself to other approaches.

**Good action improvements** focus on the ONE task:
- Clearer syntax rules
- Better examples of correct vs incorrect output
- More precise constraints for that specific technique

**How to fix**: Remove the "extra intelligence" parts. If something needs cross-call awareness or action comparison, it belongs in Router.

---

### What To Do

1. Read each revised prompt
2. Check for both problems above
3. If you find violations, **edit the files to fix them** — don't just report
4. For boundary violations: move content to Router
5. For scope creep: remove the extra parts entirely

You're done when all revised prompts pass both checks.


