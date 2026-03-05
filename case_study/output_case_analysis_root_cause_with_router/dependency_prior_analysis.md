# Phase 1: Dependency Prior Analysis

## System Overview: VeruSAGE Multi-Agent Verification Repair System

VeruSAGE is a multi-agent system for automatically repairing Verus (Rust formal verification) errors using 15 specialized agents with 24+ prompt templates. The system operates through iterative repair cycles where specialized agents reason about errors and generate repair candidates.

---

## Component Identification

### Active Components

#### 1. Decision-Makers (Routing/Planning Components)

##### **assertion_reasoning_pipeline** (Router)
- **Type**: Decision-maker / Router
- **Role**: Analyzes assertion failures and selects the best repair action from 16 options
- **Produces**:
  - Action selection decision (primary_action, secondary_actions)
  - Root cause analysis
  - Action parameters (assertion_content, guidance)
  - Reasoning explanation
- **Consumes**:
  - Current code state (last accepted version)
  - Verus error trace (assertion failure details)
  - Error location information
  - Action history (previous attempts and their outcomes - accepted/rejected)
  - Evaluation results from previous attempts
- **Note**: This is a ROUTER NODE - it does NOT generate code or have direct scores. It is evaluated indirectly through the success of the actions it selects.

##### **swap_case_compute** (Feature Flag / Decision Override)
- **Type**: Decision modifier
- **Role**: When enabled, overrides action selection if primary_action = CASE_ANALYSIS and COMPUTE is in secondary_actions, forcing COMPUTE to execute first
- **Produces**:
  - Modified action selection (actual_action = COMPUTE instead of CASE_ANALYSIS)
- **Consumes**:
  - Reasoning output (primary_action, secondary_actions)
  - Configuration flag state
- **Note**: This is a system-level policy that modifies routing decisions

#### 2. Executors (Code Generation Components)

##### **Error-Specific Agents** (15 total)
Each handles specific error types:

**PostconditionErrorAgent**
- **Error Type**: PostCondFail
- **Produces**: Code repair candidates for postcondition failures
- **Consumes**: Current code state, error trace, prompt template (postcondition_repair_basic.md or postcondition_repair_expand.md)
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

**PreconditionErrorAgent**
- **Error Type**: PreCondFail
- **Produces**: Code repairs adding precondition assertions
- **Consumes**: Current code state, error trace, prompt template (precondition_repair.md)
- **Acceptance Criteria**: FIX_PRECONDITION

**InvariantFrontErrorAgent**
- **Error Type**: InvFailFront
- **Produces**: Loop invariant repairs at entry point
- **Consumes**: Current code state, error trace, prompt template (invariant_front_repair_general.md)
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

**InvariantEndErrorAgent**
- **Error Type**: InvFailEnd
- **Produces**: Loop invariant repairs at loop end
- **Consumes**: Current code state, error trace, prompt template (invariant_end_repair.md)
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

**ArithmeticOverflowErrorAgent**
- **Error Type**: ArithmeticFlow
- **Produces**: Bounds assertions for overflow/underflow
- **Consumes**: Current code state, error trace, inline prompt
- **Acceptance Criteria**: NO_BANDAID_ASSERTS

**TypeMismatchErrorAgent**
- **Error Type**: MismatchedType
- **Produces**: Type mismatch repairs
- **Consumes**: Current code state, error trace, prompt template (type_repair.md)
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

**AssertionErrorAgent** (Two-Stage)
- **Error Type**: AssertFail
- **Stage 1 (Router)**: assertion_reasoning_pipeline (see above)
- **Stage 2 (Actions)**: Executes one of 16 assertion repair actions (see below)

##### **Assertion Repair Actions** (16 total - executed after assertion_reasoning_pipeline)

**instantiate_forall**
- **Produces**: Proof blocks transforming universal quantifiers
- **Consumes**: Current code state, action guidance from router, prompt template (instantiate_forall.md)
- **Acceptance Criteria**: ERROR_REDUCTION

**instantiate_exists**
- **Produces**: Witness provision for existential quantifiers
- **Consumes**: Current code state, action guidance from router, prompt template (instantiate_exists.md)
- **Acceptance Criteria**: ERROR_REDUCTION

**case_analysis**
- **Produces**: Proof split into conditional cases
- **Consumes**: Current code state, action guidance from router, prompt template (case_analysis.md)
- **Acceptance Criteria**: ERROR_REDUCTION
- **Note**: Can be swapped with COMPUTE by swap_case_compute feature

**reveal_opaque**
- **Produces**: Code revealing opaque function definitions
- **Consumes**: Current code state, action guidance from router, prompt template (reveal_opaque.md)
- **Acceptance Criteria**: ERROR_REDUCTION

**reveal_with_fuel**
- **Produces**: Code revealing recursive functions with fuel
- **Consumes**: Current code state, action guidance from router, prompt template (reveal_with_fuel.md)
- **Acceptance Criteria**: ERROR_REDUCTION

**extensional_equality**
- **Produces**: Element-wise collection equality proofs
- **Consumes**: Current code state, action guidance from router, prompt template (extensional_equality.md)
- **Acceptance Criteria**: ERROR_REDUCTION

**induction**
- **Produces**: Inductive proofs on data structures
- **Consumes**: Current code state, action guidance from router, prompt template (induction.md)
- **Acceptance Criteria**: ERROR_REDUCTION

**inductive_lemma**
- **Produces**: Lemmas with inductive patterns
- **Consumes**: Current code state, action guidance from router, prompt template (inductive_lemma.md)
- **Acceptance Criteria**: ERROR_REDUCTION

**compute**
- **Produces**: Computation hints for constants
- **Consumes**: Current code state, action guidance from router, prompt template (compute.md)
- **Acceptance Criteria**: ERROR_REDUCTION
- **Note**: Can be prioritized by swap_case_compute feature

**seqsetmap**
- **Produces**: Sequence/Set/Map operation repairs
- **Consumes**: Current code state, action guidance from router, prompt template (seqsetmap.md)
- **Acceptance Criteria**: ERROR_REDUCTION

**arithmetic_reasoning** (nonlinear_arithmetic)
- **Produces**: Nonlinear arithmetic proofs with by(nonlinear_arith)
- **Consumes**: Current code state, action guidance from router, prompt template (arithmetic_reasoning.md)
- **Acceptance Criteria**: ERROR_REDUCTION

**integer_ring**
- **Produces**: Integer ring property proofs
- **Consumes**: Current code state, action guidance from router, prompt template (integer_ring.md)
- **Acceptance Criteria**: ERROR_REDUCTION

**bit_vector_reasoning**
- **Produces**: Bit-vector proofs with by(bit_vector)
- **Consumes**: Current code state, action guidance from router, prompt template (bit_vector_reasoning.md)
- **Acceptance Criteria**: ERROR_REDUCTION

**add_trigger_assert**
- **Produces**: Assertions to trigger quantifiers
- **Consumes**: Current code state, action guidance from router, prompt template (add_trigger_assert.md)
- **Acceptance Criteria**: ERROR_REDUCTION

**uselemma**
- **Produces**: Invocations of existing helper lemmas
- **Consumes**: Current code state, action guidance from router, prompt template (uselemma.md)
- **Acceptance Criteria**: ERROR_REDUCTION

**loopinv**
- **Produces**: Loop invariant additions/modifications
- **Consumes**: Current code state, action guidance from router, prompt template (loopinv.md)
- **Acceptance Criteria**: DONT_AFFECT_VERIFIED

##### **Fallback Agent**
**fallback_llm_repair**
- **Error Type**: Generic (any unmatched error)
- **Produces**: Generic error repairs
- **Consumes**: Current code state, error trace, prompt template (fallback_llm_repair.md)
- **Acceptance Criteria**: VERIFICATION_IMPROVEMENT

### Passive Components (State Managers)

#### **Code State Manager**
- **Type**: Persistent state / shared memory
- **Role**: Maintains the current version of the code being repaired
- **State**: Code baseline (versioned: v0, v1, v2, ...)
- **Update Rule**: ONLY updated when a candidate is ACCEPTED
- **Key Invariant**:
  - Rejected candidates do NOT update code state
  - All subsequent actions receive the last accepted code version as input
  - Creates transitive data dependencies between all accepted actions

#### **History State Manager**
- **Type**: Metadata accumulator / shared memory
- **Role**: Records all action attempts and their outcomes
- **State**: List of (action_name, accepted/rejected) pairs
- **Update Rule**: Updated for BOTH accepted and rejected attempts
- **Usage**:
  - Provides context to routers (assertion_reasoning_pipeline) about previous attempts
  - Helps avoid repeating failed strategies
  - Does NOT store rejected code candidates, only metadata

#### **Verus Verifier** (External System Interface)
- **Type**: External verification oracle / evaluation system
- **Role**: Evaluates code candidates and produces verification scores
- **Consumes**: Code candidates from action agents
- **Produces**: EvalScore objects containing:
  - verified: int (number of verified functions)
  - errors: int (total error count)
  - timeout: bool (verification timeout)
  - compilation_error: bool (compilation failed)
- **Note**: Not a component within the multi-agent system, but an external oracle that all actions depend on for evaluation

#### **Acceptance Criteria Evaluator**
- **Type**: Policy enforcement / validation gate
- **Role**: Determines whether a candidate should be accepted based on its scores and the action's acceptance criteria
- **Consumes**:
  - Before score (from last accepted code)
  - After score (from candidate)
  - Acceptance criteria type (ERROR_REDUCTION, VERIFICATION_IMPROVEMENT, etc.)
- **Produces**:
  - Acceptance decision (accepted: true/false)
  - Acceptance reason
- **Decision Policies** (ordered by strictness):
  - COMPLETE_FIX (priority 0): Must fix ALL errors completely
  - ERROR_REDUCTION (priority 1): Must reduce total error count
  - VERIFICATION_IMPROVEMENT (priority 2): Must fix target error
  - NO_BANDAID_ASSERTS (priority 3): Fix without unsafe admits
  - FIX_PRECONDITION (priority 7): Specifically fix precondition failures
  - DONT_AFFECT_VERIFIED (priority 6): Don't break verified code

---

## Dependency Prior List

### Control Dependencies (Routing and Execution Flow)

#### CD-1: Error Type → Agent Selection
```
Error Type (system input) →ctrl Specialized Agent
```
- **Rationale**: The system routes errors to specific agents based on error type (AssertFail → AssertionErrorAgent, PostCondFail → PostconditionErrorAgent, etc.)
- **Condition**: Error type classification determines which agent/prompt is invoked

#### CD-2: assertion_reasoning_pipeline → Action Selection
```
assertion_reasoning_pipeline →ctrl {instantiate_forall, instantiate_exists, case_analysis, reveal_opaque, reveal_with_fuel, extensional_equality, induction, inductive_lemma, compute, seqsetmap, arithmetic_reasoning, integer_ring, bit_vector_reasoning, add_trigger_assert, uselemma, loopinv}
```
- **Rationale**: For AssertFail errors, the router analyzes the failure and selects which action to execute
- **Condition**: primary_action field in router output determines which action agent runs
- **Note**: This is a 1-to-16 control dependency - the router decides which ONE action executes in each repair attempt

#### CD-3: swap_case_compute → Action Override
```
swap_case_compute →ctrl {case_analysis, compute}
```
- **Rationale**: When enabled and router selects case_analysis with compute as secondary, this feature overrides to execute compute instead
- **Condition**: swap_case_compute=true AND primary_action=case_analysis AND compute ∈ secondary_actions
- **Note**: This is a policy-level control dependency that modifies routing decisions

#### CD-4: Acceptance Criteria Evaluator → Code State Update
```
Acceptance Criteria Evaluator →ctrl Code State Manager
```
- **Rationale**: The evaluator's acceptance decision determines whether Code State Manager updates to new version
- **Condition**: If accepted=true, Code State Manager updates; if accepted=false, no update occurs
- **Note**: This gate controls ALL code state transitions in the system

### Data Dependencies (Artifact Flow)

#### DD-1: Code State Manager → All Action Agents
```
Code State Manager →data {All 15 Agents + 16 Assertion Actions}
```
- **Artifact**: Current code baseline (versioned code)
- **Rationale**: Every action agent receives the last accepted code version as input for generating repair candidates
- **Critical Property**: This creates TRANSITIVE dependencies - if Action_A at position N is accepted, ALL subsequent actions at positions N+1, N+2, ... depend on Action_A's output through the Code State Manager

#### DD-2: History State Manager → assertion_reasoning_pipeline
```
History State Manager →data assertion_reasoning_pipeline
```
- **Artifact**: Action history metadata (list of previous attempts and their outcomes)
- **Rationale**: Router receives history to avoid repeating failed strategies and to understand repair context
- **Note**: History includes action names and accept/reject status, NOT the actual rejected code

#### DD-3: Verus Verifier → Acceptance Criteria Evaluator
```
Verus Verifier →data Acceptance Criteria Evaluator
```
- **Artifact**: EvalScore (verified count, error count, compilation_error, timeout)
- **Rationale**: Evaluator uses scores to determine if candidate meets acceptance criteria
- **Note**: Two scores are compared - before_score (from last accepted code) and after_score (from candidate)

#### DD-4: Action Agents → Verus Verifier
```
{All Action Agents} →data Verus Verifier
```
- **Artifact**: Code repair candidates
- **Rationale**: All action agents produce code candidates that must be verified to obtain scores
- **Note**: Each action can produce multiple candidates

#### DD-5: assertion_reasoning_pipeline → Action Agents (Assertion-specific)
```
assertion_reasoning_pipeline →data {16 Assertion Actions}
```
- **Artifact**: Action parameters (assertion_content, guidance, root_cause_analysis)
- **Rationale**: Router provides guidance and parameters to the selected action agent
- **Note**: This is guidance information, not code artifacts

#### DD-6: Verus Verifier → History State Manager
```
Verus Verifier →data History State Manager
```
- **Artifact**: Evaluation metadata (scores, acceptance status)
- **Rationale**: Verification results are logged to history for future router decisions
- **Flow**: Verus Verifier → Acceptance Criteria Evaluator → History State Manager

#### DD-7: Acceptance Criteria Evaluator → History State Manager
```
Acceptance Criteria Evaluator →data History State Manager
```
- **Artifact**: Acceptance decision and reason
- **Rationale**: Each attempt's outcome (accepted/rejected) is recorded in history

### Transitive Data Dependencies (Code-State Cascade)

#### TDD-1: Accepted Action → All Subsequent Actions (via Code State)
```
Action_i (accepted at position N) →data [Code State Manager] →data Action_j (any position > N)
```
- **Artifact**: Modified code baseline
- **Rationale**: When Action_i is accepted at position N, the Code State Manager updates to version produced by Action_i. ALL subsequent actions at positions N+1, N+2, ... receive this modified code as input.
- **Critical Consequence**:
  - If Action_i commits to a suboptimal proof direction (but still passes acceptance criteria), ALL downstream actions inherit a degraded baseline
  - This can cause "code-state cascade" failures where many different actions fail consecutively not because their prompts are bad, but because the code baseline is on the wrong proof path
  - The root cause of such cascades is the ACCEPTED action that degraded the baseline, NOT the individual failing actions
- **Example**: If `case_analysis` is accepted and expands a function into complex piecewise logic, but the correct approach was `uselemma`, then subsequent actions like `compute`, `arithmetic_reasoning`, `seqsetmap` all fail because they inherit the wrong proof structure

### Special Pattern Dependencies

#### SPD-1: Router Decision Quality → Downstream Action Success
```
assertion_reasoning_pipeline (decision quality) →indirect All subsequent assertion actions (in same trace)
```
- **Type**: Quality propagation dependency
- **Rationale**: If the router consistently selects inappropriate actions, downstream repair attempts fail not due to action prompt quality, but due to wrong action selection
- **Note**: Router "failures" manifest as failures of the actions it selects - the router itself has no direct failure signal

#### SPD-2: LLM Syntax Noise → Verus Verifier Outcome
```
Action Agent (LLM generation quality) →noise Verus Verifier (compilation_error flag)
```
- **Type**: Noise dependency (not strategy quality)
- **Rationale**: Compilation errors indicate LLM syntax generation failures, NOT repair strategy incorrectness
- **Critical Distinction**:
  - compilation_error=true → LLM syntax noise (not signal about prompt quality)
  - errors>0 && compilation_error=false → Meaningful signal about repair strategy effectiveness
- **Impact on Optimization**: Compilation errors should generally NOT be attributed to prompt quality when evaluating action effectiveness

---

## Component Classification Summary

### Active Components (Decision-Makers)
1. **assertion_reasoning_pipeline** - Router for assertion failures
2. **swap_case_compute** - Policy-based action override

### Active Components (Executors)
3. **PostconditionErrorAgent**
4. **PreconditionErrorAgent**
5. **InvariantFrontErrorAgent**
6. **InvariantEndErrorAgent**
7. **ArithmeticOverflowErrorAgent**
8. **TypeMismatchErrorAgent**
9. **instantiate_forall**
10. **instantiate_exists**
11. **case_analysis**
12. **reveal_opaque**
13. **reveal_with_fuel**
14. **extensional_equality**
15. **induction**
16. **inductive_lemma**
17. **compute**
18. **seqsetmap**
19. **arithmetic_reasoning**
20. **integer_ring**
21. **bit_vector_reasoning**
22. **add_trigger_assert**
23. **uselemma**
24. **loopinv**
25. **fallback_llm_repair**
26. (8 more error-specific agents with inline prompts)

### Passive Components (State Managers)
27. **Code State Manager** - Maintains code baseline (only updated by accepted candidates)
28. **History State Manager** - Records action attempts and outcomes
29. **Verus Verifier** - External verification oracle
30. **Acceptance Criteria Evaluator** - Policy enforcement gate

---

## Critical System Properties

### Property 1: Code State Independence
- Each repair attempt receives the SAME code baseline regardless of how many rejections occurred
- Code state only advances when acceptance occurs
- Rejected candidates are completely discarded (not even stored)

### Property 2: History State Accumulation
- All attempts (accepted AND rejected) are recorded in history
- History provides context but NOT rejected code artifacts
- Router sees "Action X was rejected" but NOT "what code did Action X generate"

### Property 3: Transitive Code Dependency
- Every accepted action creates dependencies to ALL future actions
- The dependency chain spans across different agents, error types, and positions
- Root cause of downstream failures may be upstream accepted actions, not the failing actions themselves

### Property 4: Router Indirect Evaluation
- Routers (assertion_reasoning_pipeline) have no direct failure signal
- Router effectiveness is measured through success/failure of selected actions
- A "bad routing decision" manifests as action failure, not router failure

### Property 5: Compilation vs. Verification Errors
- compilation_error=true → LLM syntax noise (not strategy signal)
- errors>0 && compilation_error=false → Meaningful strategy signal
- Optimization should focus on verification failures, not compilation errors

---

## Implications for Optimization

### For Phase 2 (Bottleneck Diagnosis)
1. When analyzing failures, check for **code-state cascade patterns**:
   - If many different actions fail consecutively at positions N+1, N+2, ..., N+K
   - And an action was ACCEPTED at position N
   - Then position N is likely the root cause (suboptimal proof direction)

2. Router (assertion_reasoning_pipeline) failures should be identified by:
   - Consistently selecting actions that fail
   - NOT by "router failure" signals (which don't exist)

3. Compilation errors should be filtered or de-weighted:
   - They reflect LLM syntax noise, not prompt quality issues

### For Phase 3 (Context Extraction)
1. When extracting failure context for action prompts:
   - Check if upstream accepted actions created a degraded baseline
   - Look for transitive dependencies through Code State Manager

2. When extracting failure context for router prompts:
   - Analyze whether selected actions consistently fail
   - Consider the quality of action parameters (guidance) provided

### For Phase 4 (Policy Evolution)
1. Action prompt optimization should consider:
   - Whether failures are due to the action's own prompt or inherited code state
   - Code-state cascade patterns indicate upstream issues, not local prompt issues

2. Router prompt optimization should focus on:
   - Action selection accuracy (choosing appropriate actions for error contexts)
   - Guidance quality (providing useful parameters to actions)

---

## End of Phase 1 Analysis
