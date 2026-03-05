# Phase 1: Dependency Prior Analysis for VeruSAGE Multi-Agent System

## System Overview

VeruSAGE is a multi-agent system for automated Verus verification repair. The system operates in an iterative loop where each repair attempt involves multiple specialized components working together to fix verification errors.

## Component Classification

### Active Components

#### 1. Decision-Makers (Routers)

**assertion_reasoning_pipeline**
- Type: Router Node
- Produces: Action selection decision (primary_action, secondary_actions), reasoning analysis
- Consumes: Current code state (last accepted version), error trace, action history
- Role: Analyzes assertion failures and selects the best repair action from 16 options

#### 2. Executors (Action Agents)

**Error-Specific Agents (7 agents)**
- postcondition_repair (PostconditionErrorAgent)
- precondition_repair (PreconditionErrorAgent)
- invariant_front_repair (InvariantFrontErrorAgent)
- invariant_end_repair (InvariantEndErrorAgent)
- type_repair (TypeMismatchErrorAgent)
- arithmetic_overflow_repair (ArithmeticOverflowErrorAgent)
- fallback_llm_repair (Generic error handler)

Each produces: Code repair candidates
Each consumes: Current code state, specific error information, prompt template

**Assertion Repair Actions (16 actions)**
- instantiate_forall: Transform universal quantifiers
- instantiate_exists: Provide witnesses for existential quantifiers
- case_analysis: Split proof into conditional cases
- reveal_opaque: Reveal opaque function definitions
- reveal_with_fuel: Reveal recursive functions with fuel
- extensional_equality: Prove collection equality element-wise
- induction: Apply induction on data structures
- inductive_lemma: Generate inductive lemmas
- compute: Add computation hints
- seqsetmap: Sequence/Set/Map operations and lemmas
- arithmetic_reasoning: Nonlinear arithmetic reasoning
- integer_ring: Integer ring properties
- bit_vector_reasoning: Bit-vector proofs
- add_trigger_assert: Add assertions to trigger quantifiers
- uselemma: Invoke existing helper lemmas
- loopinv: Add/modify loop invariants

Each produces: Code repair candidates
Each consumes: Current code state, assertion failure context, reasoning guidance

### Passive Components (State Managers)

#### 1. Code State Manager
- Type: Centralized code baseline storage
- Stores: Current verified code version (updated ONLY by accepted candidates)
- Read by: All routers and action agents
- Written by: Acceptance evaluation logic (when candidate is accepted)

#### 2. History State Manager
- Type: Action attempt log
- Stores: List of (action_name, accepted/rejected) tuples
- Read by: assertion_reasoning_pipeline (to avoid repeating failed strategies)
- Written by: Acceptance evaluation logic (for ALL attempts)

#### 3. Verus Verifier
- Type: External validation oracle
- Produces: EvalScore (verified count, error count, compilation_error flag, timeout flag)
- Consumes: Code repair candidates
- Role: Validates each candidate independently

#### 4. Acceptance Criteria Evaluator
- Type: Decision logic
- Produces: Accept/reject decision, acceptance reason
- Consumes: Before score, after score, acceptance criteria level
- Role: Determines whether a candidate is accepted based on predefined criteria

## Dependency Priors

### Control Dependencies

**CD1: Error Type → Agent Selection**
- Source: Error detection
- Target: Specific agent (postcondition_repair, precondition_repair, etc.)
- Condition: Error type classification determines which agent is invoked
- Rationale: Different error types route to specialized agents with domain-specific repair strategies

**CD2: Error Type = AssertFail → assertion_reasoning_pipeline**
- Source: Error detection (AssertFail type)
- Target: assertion_reasoning_pipeline
- Condition: Only assertion failures trigger the two-stage routing process
- Rationale: Assertion errors require sophisticated strategy selection among 16 possible actions

**CD3: assertion_reasoning_pipeline → Action Selection**
- Source: assertion_reasoning_pipeline
- Target: One of 16 assertion repair actions
- Condition: Router's primary_action decision determines which action executes
- Rationale: Router analyzes failure context and selects the most appropriate repair strategy

**CD4: swap_case_compute Flag → Action Override**
- Source: swap_case_compute configuration
- Target: case_analysis vs. compute action selection
- Condition: If primary_action = case_analysis AND compute in secondary_actions AND swap_case_compute = true, then override to compute
- Rationale: Special optimization to prefer compute over case_analysis in specific scenarios

**CD5: Acceptance Criteria → Code State Update**
- Source: Acceptance Criteria Evaluator
- Target: Code State Manager
- Condition: If candidate passes acceptance criteria, then Code State Manager is updated
- Rationale: Only accepted candidates become the new code baseline; rejected candidates do not alter code state

**CD6: Acceptance Criteria → Next Iteration Trigger**
- Source: Acceptance Criteria Evaluator
- Target: Next repair iteration (if rejected) OR next error (if accepted)
- Condition: Acceptance determines whether to retry same error or move forward
- Rationale: System loops on same error until acceptance or max attempts reached

### Data Dependencies

**DD1: Code State Manager → All Agents/Actions**
- Source: Code State Manager
- Target: All routers and action agents
- Artifact: Current code baseline (last accepted version)
- Rationale: Every repair attempt starts from the most recent accepted code, NOT from rejected candidates. This is the fundamental code-input invariant.

**DD2: History State Manager → assertion_reasoning_pipeline**
- Source: History State Manager
- Target: assertion_reasoning_pipeline
- Artifact: Action history metadata (action names and accept/reject status)
- Rationale: Router uses history to avoid repeating failed strategies, but does NOT see rejected code

**DD3: Action Agent → Verus Verifier**
- Source: Any action agent or error-specific agent
- Target: Verus Verifier
- Artifact: Generated code repair candidates
- Rationale: Each candidate must be validated to produce an EvalScore

**DD4: Verus Verifier → Acceptance Criteria Evaluator**
- Source: Verus Verifier
- Target: Acceptance Criteria Evaluator
- Artifact: EvalScore (verified, errors, compilation_error, timeout)
- Rationale: Evaluation scores determine whether a candidate satisfies acceptance criteria

**DD5: Accepted Action (position N) → All Subsequent Actions (position N+1, N+2, ...)**
- Source: Any accepted action at position N
- Target: All subsequent actions (via Code State Manager)
- Artifact: Modified code baseline
- Rationale: **Transitive Code-State Cascade** - When action A is accepted at position N, its output becomes the code input for ALL subsequent actions (until the next acceptance). This creates a transitive data dependency chain: if action A commits to a suboptimal proof direction, all downstream actions inherit that degraded baseline, even if they use completely different prompts and target different errors.

**DD6: assertion_reasoning_pipeline → Selected Action**
- Source: assertion_reasoning_pipeline
- Target: Selected action (e.g., instantiate_forall, reveal_opaque, etc.)
- Artifact: Reasoning guidance (root_cause_analysis, action_parameters)
- Rationale: Router provides context and guidance to the selected action for more informed repair

**DD7: Error Detection → All Agents**
- Source: Error detection mechanism
- Target: All agents
- Artifact: Error trace, error type, error location
- Rationale: Error information is the primary input that drives all repair attempts

### Critical Dependency Patterns

**Pattern 1: Router-Action Indirect Dependency**
- When: assertion_reasoning_pipeline (position N) → action X (position N) → rejected
- Implication: The "failure" is attributed to action X, NOT the router. Router decisions are evaluated indirectly through action success.
- Exception: If router consistently chooses inappropriate actions across many traces, then router's logic may need improvement.

**Pattern 2: Code-State Cascade (Most Critical)**
- When: Action A (position N) → accepted → multiple different actions fail at positions N+1, N+2, ..., N+K
- Implication: Action A likely committed to a suboptimal proof direction. Root cause is position N (or N's router decision), NOT the individual failing actions.
- Signal: Consecutive failures spanning MULTIPLE action types after one acceptance
- Example: case_analysis accepted → compute fails → arithmetic_reasoning fails → seqsetmap fails → root cause is the initial case_analysis acceptance

**Pattern 3: Compilation Error vs. Verification Failure**
- When: Action produces candidate with compilation_error = true
- Implication: This is LLM code generation noise (syntax error), NOT evidence that the repair strategy is wrong. Compilation errors should NOT be attributed to prompt quality.
- Contrast: Verification failures (compilation_error = false, errors > 0) ARE meaningful signals about strategy effectiveness.

**Pattern 4: State Separation Invariant**
- Invariant: code_input[attempt_N] = last_accepted_code, regardless of rejections between acceptances
- Implication: Rejected attempts do NOT contaminate future code inputs. Only history metadata is passed forward.
- Example: Attempt 1 accepted → v1 | Attempt 2 rejected → still v1 | Attempt 3 starts from v1 (NOT from attempt 2's rejected code)

## Component Interaction Flow

### Single Repair Iteration

1. **Error Detection** → routes to appropriate agent/router (CD1, CD2, DD7)
2. **Agent/Router** reads Code State Manager (DD1) and History State Manager (DD2)
3. **Router** (if applicable) selects action (CD3, CD4) and provides guidance (DD6)
4. **Action Agent** generates candidates from current code baseline (DD1, DD6)
5. **Verus Verifier** evaluates each candidate (DD3)
6. **Acceptance Criteria Evaluator** decides accept/reject (DD4)
7. If accepted: Update Code State Manager (CD5, DD5) and History State Manager
8. If rejected: Update History State Manager only
9. Next iteration (CD6)

### Key Insights for Optimization

1. **Router optimization is indirect**: Improve routers by analyzing which actions they chose and whether those actions succeeded, not by direct router failure signals.

2. **Code-state cascade detection is critical**: When multiple diverse actions fail after one acceptance, investigate the accepted action's output, not the failing actions' prompts.

3. **Compilation errors are noise**: Filter out compilation_error = true cases when evaluating action prompt quality.

4. **Transitive dependencies dominate**: The most impactful dependency is DD5 (accepted action → all subsequent actions), as it creates cascading effects that can cause widespread downstream failures.

5. **History information is limited**: Agents see action names and results, but NOT the actual rejected code, limiting their ability to learn from specific failure patterns.

## Summary Statistics

- **Decision-Makers**: 1 (assertion_reasoning_pipeline)
- **Executor Actions**: 23 (16 assertion actions + 7 error-specific agents)
- **Passive State Components**: 4 (Code State Manager, History State Manager, Verus Verifier, Acceptance Criteria Evaluator)
- **Control Dependencies**: 6 major routing and triggering decisions
- **Data Dependencies**: 7 major artifact flows
- **Critical Patterns**: 4 dependency patterns that dominate system behavior

The most critical dependency for performance analysis is **DD5 (Code-State Cascade)**, as accepted actions create transitive dependencies to ALL downstream actions, potentially causing widespread cascading failures when an action commits to a suboptimal proof direction.
