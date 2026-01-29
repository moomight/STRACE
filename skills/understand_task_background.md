# VeruSAGE: Task-Specific Multi-Agent System for Verus Verification Repair

## System Overview

**VeruSAGE** automatically repairs Verus (Rust formal verification) errors using 15 specialized agents with 24 prompt templates. Each agent handles specific error types and uses LLM-based repair strategies.

## Pipeline

```
Input → Verify → Error? → Route Agent → Reason → Select Prompt → Generate Repair → Validate → Apply
           ↑        No ↓                                                      ↓
           |     SUCCESS                                              Accept/Reject
           └─────────────────────────────────────────────────────────────┘
```

**Loop**: Verify → Fix one error → Validate → Repeat until verified or max attempts.

## Node Types in Traces

### Action Nodes vs. Router Nodes

When analyzing traces, distinguish between two types of nodes:

1. **Action Nodes** (Generate Code)
   - Produce concrete code repair candidates
   - Examples: `uselemma`, `compute`, `case_analysis`, `postcondition_repair`
   - Have evaluation scores: compilation_error, verified count, error count
   - Can be directly optimized by improving their prompts

2. **Router Nodes** (Decision Making)
   - Analyze context and select which action to call
   - Example: `assertion_reasoning_pipeline`
   - Do NOT generate code or have direct scores
   - Evaluated indirectly through the success of chosen actions or by the correctness of action choosing
   - Their "failures" are actually failure selection of the actions

**Critical for Analysis**: When a router appears in a failed trace:
- The router itself is rarely the root cause
- Look at which action it chose and whether that action failed
- Optimize the action's prompt, not the router's prompt
- Exception: If the router consistently chooses inappropriate actions across many traces, then the router's decision logic may need improvement

## Agents and Error Types

| Agent | Error Type | Stages | Prompts |
|-------|-----------|--------|---------|
| `AssertionErrorAgent` | `AssertFail` | Two-stage | Stage 1: `assertion_reasoning_pipeline.md`<br>Stage 2: 16 action prompts |
| `PreconditionErrorAgent` | `PreCondFail` | Single | `precondition_repair.md` |
| `PostconditionErrorAgent` | `PostCondFail` | Single | `postcondition_repair_*.md` |
| `InvariantFrontErrorAgent` | `InvFailFront` | Single | `invariant_front_repair_general.md` |
| `InvariantEndErrorAgent` | `InvFailEnd` | Single | `invariant_end_repair.md` |
| `ArithmeticOverflowErrorAgent` | `ArithmeticFlow` | Single | Inline in Python |
| `TypeMismatchErrorAgent` | `MismatchedType` | Single | `type_repair.md` |
| Others (8 agents) | Various | Single | `.md` or inline |

**AssertionErrorAgent is special**: Two-stage repair with routing (no scoring) then action execution (scored).

### Router vs. Action Distinction

- **Stage 1 (Router)**: `assertion_reasoning_pipeline` is a ROUTER NODE
  - Analyzes the assertion failure context
  - Selects the best action from 16 options
  - Does NOT generate code or produce scores
  - Cannot "fail" in the traditional sense (no code to verify)
  
- **Stage 2 (Action)**: The selected action is an ACTION NODE
  - Generates code repair candidates
  - Candidates are verified and scored
  - Can fail with compilation errors or verification failures
  - This is where actual repair quality is measured

## Prompts and Acceptance Criteria

### Routing Prompt (No Acceptance Criteria)

| Prompt | Description |
|--------|-------------|
| `assertion_reasoning_pipeline.md` | Analyzes assertion failures, selects best action from 16 options. **NO scoring at this stage** - pure routing decision. The selected action then generates candidates which are scored and evaluated. Critical for repair success.|

### Assertion Action Prompts (16 total)

| Prompt | Description | Acceptance Criteria |
|--------|-------------|---------------------|
| `instantiate_forall.md` | Transform universal quantifiers to proof blocks | `ERROR_REDUCTION` |
| `instantiate_exists.md` | Provide witness for existential quantifiers | `ERROR_REDUCTION` |
| `case_analysis.md` | Split proof into conditional cases | `ERROR_REDUCTION` |
| `reveal_opaque.md` | Reveal opaque function definitions | `ERROR_REDUCTION` |
| `reveal_with_fuel.md` | Reveal recursive functions with fuel | `ERROR_REDUCTION` |
| `extensional_equality.md` | Prove collection equality element-wise | `ERROR_REDUCTION` |
| `induction.md` | Apply induction on data structures | `ERROR_REDUCTION` |
| `inductive_lemma.md` | Generate lemmas with inductive patterns | `ERROR_REDUCTION` |
| `compute.md` | Add computation hints for constants | `ERROR_REDUCTION` |
| `seqsetmap.md` | Sequence/Set/Map operations and lemmas | `ERROR_REDUCTION` |
| `arithmetic_reasoning.md` | Nonlinear arithmetic with `by(nonlinear_arith)` | `ERROR_REDUCTION` |
| `integer_ring.md` | Integer ring properties | `ERROR_REDUCTION` |
| `bit_vector_reasoning.md` | Bit-vector proofs with `by(bit_vector)` | `ERROR_REDUCTION` |
| `add_trigger_assert.md` | Add assertions to trigger quantifiers | `ERROR_REDUCTION` |
| `uselemma.md` | Invoke existing helper lemmas | `ERROR_REDUCTION` |
| `loopinv.md` | Add/modify loop invariants | `DONT_AFFECT_VERIFIED` |

### Error-Specific Prompts (7 total)

| Prompt | Error Type | Description | Acceptance Criteria |
|--------|-----------|-------------|---------------------|
| `precondition_repair.md` | `PreCondFail` | Add assertions for preconditions | `FIX_PRECONDITION` |
| `postcondition_repair_basic.md` | `PostCondFail` | Strengthen postconditions | `VERIFICATION_IMPROVEMENT` |
| `postcondition_repair_expand.md` | `PostCondFail` | Alternative postcondition fix | `VERIFICATION_IMPROVEMENT` |
| `invariant_front_repair_general.md` | `InvFailFront` | Fix loop invariant at entry | `VERIFICATION_IMPROVEMENT` |
| `invariant_end_repair.md` | `InvFailEnd` | Fix loop invariant at end | `VERIFICATION_IMPROVEMENT` |
| `type_repair.md` | `MismatchedType` | Fix type mismatches | `VERIFICATION_IMPROVEMENT` |
| `fallback_llm_repair.md` | Generic | Generic error repair | `VERIFICATION_IMPROVEMENT` |

### Inline Prompts (in Python files)

| Error Type | Description | Acceptance Criteria |
|-----------|-------------|---------------------|
| `ArithmeticFlow` | Add bounds assertions for overflow/underflow | `NO_BANDAID_ASSERTS` |
| `BitVAssertFail` | Fix bit-vector assertions with requires | `VERIFICATION_IMPROVEMENT` |
| `TerminationFail` | Assert decreases clause for recursion | `VERIFICATION_IMPROVEMENT` |
| `DecFailEnd` | Fix decreases clause at loop end | `VERIFICATION_IMPROVEMENT` |
| `LoopNoDec` | Add missing decreases clause | `VERIFICATION_IMPROVEMENT` |
| `UnsupportedForBitVector` | Rewrite unsupported bit-vector syntax | `VERIFICATION_IMPROVEMENT` |
| `PreCondFail` (vec) | Add vector length invariants | `FIX_PRECONDITION` |
| Other | Plain text error repair | `VERIFICATION_IMPROVEMENT` |

## Acceptance Criteria

After repair generation, each candidate is validated:

| Criteria | Description | Priority |
|----------|-------------|----------|
| `COMPLETE_FIX` | Must fix ALL errors completely | 0 (strictest) |
| `ERROR_REDUCTION` | Must reduce total error count | 1 |
| `VERIFICATION_IMPROVEMENT` | Must fix target error | 2 |
| `NO_BANDAID_ASSERTS` | Fix without unsafe admits | 3 |
| `FIX_PRECONDITION` | Specifically fix precondition failures | 7 |
| `DONT_AFFECT_VERIFIED` | Don't break verified code | 6 (loosest) |

Lower priority number = stricter validation.

## ⚙️ Special Features

### swap_case_compute

**Purpose**: Optimize action selection for specific scenarios

**Behavior**: When enabled (`--swap-case-compute`):
```python
if reasoning.primary_action == CASE_ANALYSIS and COMPUTE in reasoning.secondary_actions:
    # Override: Try COMPUTE first instead of CASE_ANALYSIS
    actual_action = COMPUTE

### Code State vs. History Information

**CRITICAL CONCEPT**: Rejected actions do NOT change code state, but DO provide history information.

```
Original Code (v0)
    |
    v
[Attempt 1: Reasoning + Action A] → Candidate → [Accepted] → Code v1
    |                                                           |
    v                                                           v
History: [A: accepted]                                   Code Baseline: v1
    |
    v  
[Attempt 2: Reasoning + Action B] → Candidate → [Rejected] → Still Code v1
    |                                                            |
    v                                                            v
History: [A: accepted, B: rejected]                       Code Baseline: v1 (unchanged!)
    |
    v
[Attempt 3: Reasoning + Action C] → Candidate → [Accepted] → Code v2
    |                                                           |
    v                                                           v
History: [A: accepted, B: rejected, C: accepted]         Code Baseline: v2
```

**Key Points**:
- **Code Baseline**: ONLY updated when a candidate is accepted
  - Attempt 2's rejection means code stays at v1
  - Attempt 3 starts reasoning from code v1, NOT v0
- **History Information**: ALL attempts (accepted/rejected) are recorded
  - Attempt 3's reasoning receives: "Previously tried A (accepted), B (rejected)"
  - This helps avoid repeating failed strategies
- **Input Independence**: Each (reasoning, action) segment receives:
  - ✅ The last accepted code version (v1)
  - ✅ History of which actions were tried and their results
  - ❌ NOT the rejected code candidates themselves
- **No Code Contamination**: Rejected candidates are discarded completely
  - Attempt 2's rejected candidate does NOT influence Attempt 3's input code
  - Only the history metadata (action name, acceptance status) is passed forward

## 📊 Evaluation and Scoring

### EvalScore Structure

```python
@dataclass
class EvalScore:
    verified: int           # Number of verified functions
    errors: int            # Total error count
    timeout: bool          # Verification timeout
    compilation_error: bool # Compilation failed
```

### Candidate Evaluation

For each repair candidate:
1. **Run Verus verification**
2. **Extract scores**: verified count, error count
3. **Apply acceptance criteria**
4. **Select best candidate** based on:
   - Acceptance status
   - Error reduction
   - Verified function count

## 🔄 Repair Process Flow

### Critical Design Principle: State Separation

**⚠️ CODE STATE vs. HISTORY STATE**: The system maintains two separate states:
1. **Code State**: Only updated by accepted candidates
2. **History State**: Records all action attempts (both accepted and rejected)

**Key Invariant**: `code_input[attempt_N] = last_accepted_code` regardless of how many rejections occurred between acceptances.

### Single Repair Attempt

```python
# Each attempt receives:
# 1. The last ACCEPTED code (unchanged by rejected attempts)
# 2. History of previous actions (both accepted and rejected)

last_accepted_code = get_last_accepted_version()  # NOT affected by rejected attempts
action_history = get_action_history()              # Includes: [(action_name, accepted/rejected), ...]

# 1. Observe (analyze ACCEPTED code state + current error)
observation = agent.observe(last_accepted_code, current_error)

# 2. Reason (receives HISTORY but not rejected code)
# The reasoning can see: "Action X was tried and rejected"
# The reasoning CANNOT see: "What code did Action X generate"
reasoning = agent.reason(observation, action_history)

# 3. Act (generate candidates from ACCEPTED baseline)
action_result = agent.act(last_accepted_code, reasoning)

# 4. Evaluate candidates independently
for candidate in action_result.candidates:
    score = evaluate_code(candidate)
    accepted, reason = evaluate_acceptance(before_score, score, action_result)
    
    if accepted:
        last_accepted_code = candidate      # Update CODE state
        action_history.append((action, 'accepted'))  # Update HISTORY state
        break  # Move to next error
    else:
        action_history.append((action, 'rejected'))  # Update HISTORY state only
        # last_accepted_code remains UNCHANGED

# Result: 
# - If accepted: Next attempt sees new code + extended history
# - If rejected: Next attempt sees SAME code + extended history
```

## 🎯 Key Takeaways

1. **Multi-Agent Architecture**: Specialized agents for each error type
2. **40+ Repair Actions**: Comprehensive coverage of Verus error patterns
3. **LLM-Driven Reasoning**: Intelligent action selection with root cause analysis
4. **Acceptance Criteria**: 7-level priority system for evaluating repairs
5. **Dual-State System**: Separates code state (only updated by acceptances) from history state (records all attempts)
6. **Code State Invariant**: Each attempt starts from the last accepted code, never from rejected candidates
7. **History Awareness**: Reasoning receives action history (accepted/rejected) but NOT the rejected code itself
8. **Special Modes**: `swap_case_compute`, tree search, target action override
9. **Self-Contained Actions**: Each action is a complete implementation

This architecture enables **systematic, explainable, and effective** automated repair of complex formal verification errors.

---

## ⚠️ Common Misconceptions

### ❌ WRONG: "The system learns from failures"
The system does NOT adapt by analyzing failed code. It only knows "Action X was tried and rejected".

### ✅ CORRECT: "The system maintains separated code and history states"
Code state = last accepted version. History state = list of (action, result) pairs. They are updated independently.

### ❌ WRONG: "Failed actions influence next reasoning by showing failed code"
The reasoning receives action names and results (rejected/accepted), NOT the actual rejected code candidates.

### ✅ CORRECT: "Rejected actions leave code unchanged but update history"
If Action B is rejected:
- Code stays at the last accepted version (e.g., v1)
- History is updated: "B was tried and rejected"
- Next attempt receives: same code v1 + updated history

### ❌ WRONG: "Each segment is completely independent with no memory"
FALSE. There IS memory, but it's limited to metadata (action history), not code artifacts.

### ✅ CORRECT: "Code input is independent; history input is cumulative"
- Code input: Always the last accepted baseline (rejected attempts don't change it)
- History input: Cumulative list of all attempted actions and their results

