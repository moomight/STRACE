# Phase 1: Graph-based Environment Modeling
## Dependency Prior Analysis for VeruSAGE Multi-Agent System

### System Overview
VeruSAGE is a task-specific multi-agent system for automated Verus verification repair. It uses 15 specialized agents with 24 prompt templates to fix formal verification errors iteratively.

---

## Component Identification

### Active Components

#### 1. Decision-Makers (Routers)

**Router: assertion_reasoning_pipeline**
- **Role**: Analyzes assertion failures and selects the best action from 16 available repair strategies
- **Produces**:
  - Action selection decision (primary_action, secondary_actions)
  - Root cause analysis
  - Reasoning explanation
  - Action parameters (guidance)
- **Consumes**:
  - Current code baseline (last accepted version)
  - Verification error trace (AssertFail type)
  - Action history (previously attempted actions and their results)
  - Code context (preconditions, assertions, function definitions)
- **Functional Role**: Two-stage repair coordinator for AssertionErrorAgent

#### 2. Executors (Action Nodes)

**Action Group A: Assertion Repair Actions (16 actions)**

**A1. instantiate_forall**
- **Produces**: Code repair candidate (proof blocks instantiating universal quantifiers), EvalScore
- **Consumes**: Code baseline, assertion content, guidance, error context
- **Acceptance Criteria**: ERROR_REDUCTION

**A2. instantiate_exists**
- **Produces**: Code repair candidate (witness provision for existentials), EvalScore
- **Consumes**: Code baseline, assertion content, guidance, error context
- **Acceptance Criteria**: ERROR_REDUCTION

**A3. case_analysis**
- **Produces**: Code repair candidate (proof split into conditional cases), EvalScore
- **Consumes**: Code baseline, assertion content, guidance, error context
- **Acceptance Criteria**: ERROR_REDUCTION

**A4. reveal_opaque**
- **Produces**: Code repair candidate (opaque function revelation), EvalScore
- **Consumes**: Code baseline, assertion content, guidance, error context
- **Acceptance Criteria**: ERROR_REDUCTION

**A5. reveal_with_fuel**
- **Produces**: Code repair candidate (recursive function revelation with fuel), EvalScore
- **Consumes**: Code baseline, assertion content, guidance, error context
- **Acceptance Criteria**: ERROR_REDUCTION

**A6. extensional_equality**
- **Produces**: Code repair candidate (element-wise equality proof), EvalScore
- **Consumes**: Code baseline, assertion content, guidance, error context
- **Acceptance Criteria**: ERROR_REDUCTION

**A7. induction**
- **Produces**: Code repair candidate (inductive proofs), EvalScore
- **Consumes**: Code baseline, assertion content, guidance, error context
- **Acceptance Criteria**: ERROR_REDUCTION

**A8. inductive_lemma**
- **Produces**: Code repair candidate (lemmas with inductive patterns), EvalScore
- **Consumes**: Code baseline, assertion content, guidance, error context
- **Acceptance Criteria**: ERROR_REDUCTION

**A9. compute**
- **Produces**: Code repair candidate (computation hints for constants), EvalScore
- **Consumes**: Code baseline, assertion content, guidance, error context
- **Acceptance Criteria**: ERROR_REDUCTION

**A10. seqsetmap**
- **Produces**: Code repair candidate (sequence/set/map operations and lemmas), EvalScore
- **Consumes**: Code baseline, assertion content, guidance, error context
- **Acceptance Criteria**: ERROR_REDUCTION

**A11. arithmetic_reasoning**
- **Produces**: Code repair candidate (nonlinear arithmetic proofs), EvalScore
- **Consumes**: Code baseline, assertion content, guidance, error context
- **Acceptance Criteria**: ERROR_REDUCTION

**A12. integer_ring**
- **Produces**: Code repair candidate (integer ring property proofs), EvalScore
- **Consumes**: Code baseline, assertion content, guidance, error context
- **Acceptance Criteria**: ERROR_REDUCTION

**A13. bit_vector_reasoning**
- **Produces**: Code repair candidate (bit-vector proofs), EvalScore
- **Consumes**: Code baseline, assertion content, guidance, error context
- **Acceptance Criteria**: ERROR_REDUCTION

**A14. add_trigger_assert**
- **Produces**: Code repair candidate (trigger assertions for quantifiers), EvalScore
- **Consumes**: Code baseline, assertion content, guidance, error context
- **Acceptance Criteria**: ERROR_REDUCTION

**A15. uselemma**
- **Produces**: Code repair candidate (lemma invocations), EvalScore
- **Consumes**: Code baseline, assertion content, guidance, error context
- **Acceptance Criteria**: ERROR_REDUCTION

**A16. loopinv**
- **Produces**: Code repair candidate (loop invariant additions/modifications), EvalScore
- **Consumes**: Code baseline, assertion content, guidance, error context
- **Acceptance Criteria**: DONT_AFFECT_VERIFIED

**Action Group B: Error-Specific Repair Actions (7 actions)**

**B1. precondition_repair**
- **Produces**: Code repair candidate (precondition assertions), EvalScore
- **Consumes**: Code baseline, PreCondFail error trace, error location
- **Acceptance Criteria**: FIX_PRECONDITION

**B2. postcondition_repair_basic**
- **Produces**: Code repair candidate (strengthened postconditions), EvalScore
- **Consumes**: Code baseline, PostCondFail error trace, error location
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

**B3. postcondition_repair_expand**
- **Produces**: Code repair candidate (alternative postcondition fix), EvalScore
- **Consumes**: Code baseline, PostCondFail error trace, error location
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

**B4. invariant_front_repair_general**
- **Produces**: Code repair candidate (loop invariant entry fix), EvalScore
- **Consumes**: Code baseline, InvFailFront error trace, error location
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

**B5. invariant_end_repair**
- **Produces**: Code repair candidate (loop invariant end fix), EvalScore
- **Consumes**: Code baseline, InvFailEnd error trace, error location
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

**B6. type_repair**
- **Produces**: Code repair candidate (type mismatch fixes), EvalScore
- **Consumes**: Code baseline, MismatchedType error trace, error location
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

**B7. fallback_llm_repair**
- **Produces**: Code repair candidate (generic error repair), EvalScore
- **Consumes**: Code baseline, generic error trace, error location
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

**Action Group C: Inline Repair Actions (8 actions)**

**C1. arithmetic_overflow_repair**
- **Produces**: Code repair candidate (bounds assertions for overflow/underflow), EvalScore
- **Consumes**: Code baseline, ArithmeticFlow error trace, error location
- **Acceptance Criteria**: NO_BANDAID_ASSERTS

**C2. bitvector_assert_repair**
- **Produces**: Code repair candidate (bit-vector assertion fixes), EvalScore
- **Consumes**: Code baseline, BitVAssertFail error trace, error location
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

**C3. termination_repair**
- **Produces**: Code repair candidate (decreases clause assertions), EvalScore
- **Consumes**: Code baseline, TerminationFail error trace, error location
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

**C4. decreases_end_repair**
- **Produces**: Code repair candidate (decreases clause end fixes), EvalScore
- **Consumes**: Code baseline, DecFailEnd error trace, error location
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

**C5. loopnodec_repair**
- **Produces**: Code repair candidate (missing decreases clause), EvalScore
- **Consumes**: Code baseline, LoopNoDec error trace, error location
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

**C6. unsupported_bitvector_repair**
- **Produces**: Code repair candidate (rewritten bit-vector syntax), EvalScore
- **Consumes**: Code baseline, UnsupportedForBitVector error trace, error location
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

**C7. precondition_vec_repair**
- **Produces**: Code repair candidate (vector length invariants), EvalScore
- **Consumes**: Code baseline, PreCondFail (vec) error trace, error location
- **Acceptance Criteria**: FIX_PRECONDITION

**C8. other_error_repair**
- **Produces**: Code repair candidate (plain text error repair), EvalScore
- **Consumes**: Code baseline, other error trace, error location
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

### Passive Components (State Managers)

**State Component 1: Code State Manager**
- **Role**: Maintains the current verified code baseline
- **State**: Current code version (only updated by accepted candidates)
- **Read by**: All routers and actions (as code input)
- **Written by**: Candidate Evaluator (only when candidate is accepted)
- **Critical Property**: Rejected candidates do NOT update this state

**State Component 2: History State Manager**
- **Role**: Tracks all action attempts and their outcomes
- **State**: Action history list [(action_name, accepted/rejected), ...]
- **Read by**: assertion_reasoning_pipeline router (for action selection)
- **Written by**: Candidate Evaluator (after each attempt, regardless of outcome)
- **Critical Property**: Cumulative - includes both accepted and rejected attempts

**State Component 3: Verus Verifier**
- **Role**: External verification oracle
- **Produces**: EvalScore (verified count, error count, compilation_error, timeout)
- **Consumes**: Code repair candidate
- **Critical Property**: Independent evaluation for each candidate

**State Component 4: Candidate Evaluator**
- **Role**: Applies acceptance criteria and updates state
- **Produces**: Acceptance decision (accepted/rejected) + reason
- **Consumes**: EvalScore (before/after), acceptance criteria, code candidate
- **Updates**: Code State Manager (if accepted), History State Manager (always)

---

## Dependency Priors

### Control Dependencies (Router → Action Selection)

**CD1: assertion_reasoning_pipeline →ctrl [A1-A16]**
- **Condition**: Router selects primary_action from 16 assertion repair strategies
- **Rationale**: Router decision determines which action executes for AssertFail errors
- **Strength**: STRONG - Router is the exclusive gatekeeper for assertion repairs

**CD2: Error Type Classifier →ctrl [B1-B7, C1-C8]**
- **Condition**: Error type (PreCondFail, PostCondFail, InvFailFront, etc.) determines agent selection
- **Rationale**: Single-stage agents are directly selected based on error type matching
- **Strength**: STRONG - Deterministic mapping from error type to agent

**CD3: swap_case_compute Override →ctrl [A3, A9]**
- **Condition**: If enabled and router selects case_analysis + compute in secondary, override to compute
- **Rationale**: Special heuristic to prioritize compute over case_analysis
- **Strength**: MEDIUM - Optional system-level override

### Data Dependencies (Direct Code Artifacts)

**DD1: [Any Action at position N] →data [Any Action at position N+M] (if action at N accepted)**
- **Artifact**: Code baseline (code state)
- **Rationale**: TRANSITIVE CODE-STATE CASCADE - When an action at position N is accepted, its code output becomes the baseline for ALL subsequent actions at positions N+1, N+2, ..., N+M. This is the fundamental dependency in the system.
- **Strength**: CRITICAL - Every accepted action creates a transitive dependency to all future actions

**DD2: assertion_reasoning_pipeline →data [A1-A16]**
- **Artifact**: Guidance text, assertion_content, action parameters
- **Rationale**: Router output provides input parameters for selected action's LLM prompt
- **Strength**: STRONG - Action execution depends on router's reasoning output

**DD3: [All Actions] →data Verus Verifier**
- **Artifact**: Code repair candidate
- **Rationale**: Actions produce code that must be verified
- **Strength**: STRONG - All actions depend on external verification

**DD4: Verus Verifier →data Candidate Evaluator**
- **Artifact**: EvalScore (verified, errors, compilation_error, timeout)
- **Rationale**: Verification results feed into acceptance decision
- **Strength**: STRONG - Evaluator requires scores for decision

**DD5: Candidate Evaluator →data Code State Manager**
- **Artifact**: Accepted code candidate
- **Rationale**: Only accepted candidates update the code baseline
- **Strength**: STRONG - Code state changes depend on evaluator's acceptance

**DD6: Candidate Evaluator →data History State Manager**
- **Artifact**: Action attempt record (action_name, result)
- **Rationale**: Every attempt (accepted or rejected) is logged
- **Strength**: STRONG - History updates depend on evaluator's decision

**DD7: Code State Manager →data [All Routers and Actions]**
- **Artifact**: Current code baseline
- **Rationale**: All reasoning and action generation starts from the last accepted code
- **Sensitive**: Code input is INDEPENDENT of rejected attempts (rejected code is discarded)
- **Strength**: STRONG - Stateful dependency for all components

**DD8: History State Manager →data assertion_reasoning_pipeline**
- **Artifact**: Action history metadata
- **Rationale**: Router uses history to avoid repeating failed strategies
- **Sensitive**: History includes attempt names and results, NOT rejected code content
- **Strength**: MEDIUM - Influences router's action selection

### State Isolation Constraints

**SI1: Code State Isolation (Rejected Attempts)**
- **Invariant**: code_input[attempt_N] = last_accepted_code, regardless of rejections between acceptances
- **Implication**: Rejected actions at positions N+1, N+2, ..., N+K do NOT change the code baseline for position N+K+1
- **Critical for**: Understanding that failures don't contaminate the code state

**SI2: History State Accumulation**
- **Invariant**: History is cumulative across all attempts
- **Implication**: History at position N includes all attempts from positions 1 to N-1
- **Critical for**: Router's ability to learn from past failures (metadata only)

### Special Dependency Patterns

**SP1: Code-State Cascade Pattern (Root Cause Propagation)**
- **Pattern**: Action A (accepted at position N) → Code State Manager → Actions B, C, D (fail at positions N+1, N+2, N+3)
- **Rationale**: If multiple DIFFERENT actions fail consecutively after an accepted action, the root cause is likely the accepted action's suboptimal code direction, NOT the individual failing actions
- **Example**: case_analysis accepted → complex piecewise code → compute fails, arithmetic_reasoning fails, seqsetmap fails (all inherit degraded baseline)
- **Implication**: When localizing failures, trace back to the most recent accepted action that changed the code state

**SP2: Router-Action Separation (Indirect Scoring)**
- **Pattern**: assertion_reasoning_pipeline (router, no score) → selects action → action generates candidates → action is scored
- **Rationale**: Router nodes have NO direct EvalScore (they don't generate code); only actions produce verifiable candidates
- **Implication**: Router "failure" is actually the failure of the action it selected; optimize the action prompt, not the router (unless router consistently chooses wrong actions)

**SP3: Compilation Noise vs. Strategy Failure**
- **Pattern**: Action produces candidate → Verus Verifier → compilation_error=True
- **Rationale**: Compilation errors are LLM syntax generation noise, NOT evidence of wrong repair strategy
- **Implication**: Only verification failures (errors > 0, compilation_error=False) reflect action prompt quality; compilation errors should be filtered out in prompt optimization

**SP4: Acceptance Does Not Guarantee Optimality**
- **Pattern**: Action A accepted (passes ERROR_REDUCTION) → Code State Manager updates → Subsequent actions fail repeatedly
- **Rationale**: Acceptance criteria only check local error reduction, not global proof strategy optimality
- **Implication**: Accepted actions can commit to suboptimal proof paths that make remaining errors harder to fix

---

## Summary of Implicit Graph Structure

### Node Types
1. **1 Router Node**: assertion_reasoning_pipeline (decision-maker for AssertFail errors)
2. **31 Action Nodes**: 16 assertion actions + 7 error-specific actions + 8 inline actions (executors)
3. **4 Passive State Nodes**: Code State Manager, History State Manager, Verus Verifier, Candidate Evaluator

### Edge Types
- **Control Edges** (3 types): Router selection, error type routing, system overrides
- **Data Edges** (8 direct types): Code artifacts, evaluation scores, state updates, parameters
- **Transitive Edges** (1 critical type): Code-state cascade from any accepted action to all subsequent actions

### Critical Causality Insights

1. **Code State is the Central Artifact**: All actions read from and (if accepted) write to the shared code baseline. This creates a LINEAR DEPENDENCY CHAIN where position matters.

2. **Routers are Metadata Producers**: Routers do not generate code; they generate action selection decisions and guidance parameters. They are evaluated indirectly through the success of their selected actions.

3. **Acceptance Creates Transitive Dependencies**: When action A at position N is accepted, it creates a data dependency to ALL future actions (N+1, N+2, ...) via the Code State Manager. This is the most critical dependency for failure localization.

4. **History Provides Weak Feedback**: History state allows routers to see what was tried before, but it only provides metadata (action names, results), not the actual rejected code. This limits the system's ability to learn from specific failure patterns.

5. **Compilation Errors are Noise**: Compilation failures do not reflect prompt quality; only verification failures (compilable code with errors > 0) should be used for prompt optimization.

6. **Code-State Cascade Failures**: When multiple different actions fail consecutively after an accepted action, the root cause is likely the accepted action's code (suboptimal proof direction), not the failing actions' prompts.

---

## Next Phase Implications

For **Phase 2: Statistical Bottleneck Diagnosis**, the dependency priors suggest:

1. **Trace-Level Analysis**: Group traces by final status (success/failure) and identify which actions/routers appear in failed vs. successful traces.

2. **Position-Aware Failure Analysis**: When analyzing failures, consider the position in the repair sequence:
   - Early failures (positions 1-3): Likely root cause issues (wrong initial action or router decision)
   - Mid-sequence failures (positions 4-10): Likely code-state cascade from earlier accepted actions
   - Late-sequence failures (positions > 10): Likely stuck in suboptimal proof path

3. **Code-State Cascade Detection**: Look for patterns where:
   - Action A is accepted at position N
   - Multiple different actions fail at positions N+1, N+2, ..., N+K
   - This suggests Action A's code degraded the baseline (optimize position N's decision or action prompt)

4. **Router vs. Action Attribution**: When assertion_reasoning_pipeline appears in failed traces:
   - First check: Did the selected action fail due to a bad prompt (verification failures)?
   - Second check: Did the router consistently choose inappropriate actions across many traces?
   - Only optimize router if there's evidence of systematic action selection errors

5. **Filter Compilation Noise**: Exclude compilation errors from failure analysis; focus on verification failures (compilation_error=False, errors > 0).

---

**End of Phase 1: Graph-based Environment Modeling**
