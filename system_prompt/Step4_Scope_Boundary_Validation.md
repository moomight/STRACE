# Step4: Validate Revised Prompts

Read `skills/understand_task_background.md` first to understand the system architecture.

Then check each revised prompt in `output/prompts_revised/` for two types of problems:

---

## Problem 1: Router vs Action Boundary Violations

**Router** decides WHICH action to call. **Action** executes HOW to apply one technique.

If an Action prompt mentions other action names, that's a violation. For example:

❌ Bad: "Try case_analysis AFTER induction and uselemma fail"  
❌ Bad: "When NOT to use me: prefer reveal_opaque first"

These belong in Router, not Action. The action doesn't know what other actions exist — it just does its job when called.

**How to fix**: Remove the cross-action content from the Action prompt, add it to the Router prompt that invokes this action.

---

## Problem 2: Action Doing Too Much

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

## What To Do

1. Read each revised prompt
2. Check for both problems above
3. If you find violations, **edit the files to fix them** — don't just report
4. For boundary violations: move content to Router
5. For scope creep: remove the extra parts entirely

You're done when all revised prompts pass both checks.
