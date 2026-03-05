# Phase 3: Causal Context Extraction Report

## Executive Summary

Phase 3 performed causal backtracking analysis to identify the root causes of failures in the VeruSAGE multi-agent system. Through systematic analysis of execution traces and causal dependency chains, we discovered that **instantiate_forall** failures were primarily caused by upstream accepted nodes that degraded the proof baseline.

**Key Finding**: The high failure rate of `instantiate_forall` (selected in Phase 2) was NOT due to its own prompt, but due to incomplete proofs accepted by `uselemma` and earlier `instantiate_forall` attempts that degraded the code baseline.

## Phase 3.1: Representative Traces Sampling

### Selected Subagent
- **instantiate_forall** (from Phase 2 high priority components)

### Sampled Traces
- **Trace**: `NR__impl_u__os_refinement__no_overlaps_pmem_applied_mappings-20251128-0.json`
- **Total positions**: 37
- **Failure pattern**: Repeated rejections of `instantiate_forall` attempts (14 rejections total)

## Phase 3.2: Backward Causal Slicing

### Execution Sequence Analysis

The trace contains the following state-changing (accepted) positions:
1. Position 1: `postcondition_repair` (accepted)
2. Position 3: `reveal_opaque` (accepted)
3. Position 5: `instantiate_forall` (accepted)
4. Position 9: `uselemma` (accepted)
5. Position 29: `instantiate_forall` (accepted)

### Causal Segments

**Segment 1**: Positions [11, 13, 15, 17, 19, 21, 23, 27]
- Representative position: 11
- Causal chain: [1, 3, 5, 9, 11]
- Pattern: 8 consecutive rejections of `instantiate_forall` after position 9 acceptance

**Segment 2**: Positions [31, 33, 35, 37]
- Representative position: 31
- Causal chain: [1, 3, 5, 9, 29, 31]
- Pattern: 4 consecutive rejections of `instantiate_forall` after position 29 acceptance

## Phase 3.3: Failure Attribution

### Segment 1 Root Cause Analysis

**Manifestation**: Positions 11-27 show repeated `instantiate_forall` failures trying to prove the overlap invariant.

**Causal Chain Investigation**:
- Position 1 (postcondition_repair): Added basic assertion - appropriate action
- Position 3 (reveal_opaque): Revealed `extra_mappings` definition - necessary and correct
- Position 5 (instantiate_forall): Instantiated forall with 4-case analysis structure - correct approach
- Position 9 (uselemma): Added `vaddr_distinct(c, s)` call - **INCOMPLETE**
- Position 11 (instantiate_forall): Rejected - tries to complete position 9's incomplete proof

**Root Cause**: Position 9 (`uselemma`)

**Detailed Analysis**:
The `uselemma` agent at position 9 correctly identified the need for `vaddr_distinct` lemma but failed to complete the proof connection. The accepted output shows:
```rust
assert(c1 != c2) by {
    vaddr_distinct(c, s);
}
assert(!overlap(...));  // This assert fails!
```

The agent added the lemma call and derived `c1 != c2`, but did NOT show how to use this fact together with `inv_inflight_pmem_no_overlap_inflight_pmem(c)` to derive `!overlap(...)`. This left an incomplete proof structure that all downstream `instantiate_forall` attempts (positions 11-27) struggled to complete.

**Why this is a root cause**:
- The `uselemma` agent's own reasoning was flawed - it should have connected the lemma result to the goal
- A different, better completion at position 9 would have closed the proof
- The accepted output degraded the baseline, creating a harder problem for downstream agents

### Segment 2 Root Cause Analysis

**Manifestation**: Positions 31-37 show continued `instantiate_forall` failures with even more complex proof structures.

**Causal Chain Investigation**:
- Positions 1-9: Same as Segment 1
- Position 29 (instantiate_forall): Accepted - introduced contrapositive reasoning but **INCORRECTLY IMPLEMENTED**
- Position 31 (instantiate_forall): Rejected - tries alternative instantiation approach

**Root Cause**: Position 29 (`instantiate_forall`)

**Detailed Analysis**:
The `instantiate_forall` agent at position 29 attempted to use proof-by-contradiction (contrapositive), introducing:
```rust
assert(!overlap(...)) by {
    assert(c1 == c2) by {  // Try to derive this assuming overlap
        assert(overlap(...));  // But this creates circular reasoning
    };
    assert(c1 != c2) by { vaddr_distinct(c, s); };
    // Expecting contradiction, but quantifier instantiation is wrong
}
```

This approach introduced a more complex nested proof structure but failed to correctly instantiate the quantified invariant `inv_inflight_pmem_no_overlap_inflight_pmem(c)`. The accepted output made the proof harder, further degrading the baseline.

**Why this is a root cause**:
- The `instantiate_forall` agent committed to a proof strategy (contrapositive) that it could not execute correctly
- The accepted output at position 29 created an even worse baseline than position 9
- Subsequent attempts (positions 31-37) inherited this degraded baseline

## Phase 3.4: Root Cause Localization

### Final Root Cause Components

Two distinct components were identified as root causes requiring prompt optimization:

#### 1. uselemma
- **Trace**: `NR__impl_u__os_refinement__no_overlaps_pmem_applied_mappings-20251128-0.json`
- **Location**: Position 9
- **Issue**: Added lemma call but did not complete proof bridge
- **Impact**: 8 downstream rejections (positions 11-27)

**Required Prompt Fix**:
The `uselemma` prompt should guide the agent to not just call the lemma, but to explicitly show how the lemma's conclusion connects to the current proof goal. When using a lemma that proves `P`, the agent must add intermediate assertions showing how `P` relates to the goal `Q`.

#### 2. instantiate_forall
- **Trace**: `NR__impl_u__os_refinement__no_overlaps_pmem_applied_mappings-20251128-0.json`
- **Location**: Position 29
- **Issue**: Incorrect contrapositive/proof-by-contradiction implementation
- **Impact**: 4 downstream rejections (positions 31-37)

**Required Prompt Fix**:
The `instantiate_forall` prompt should include clear guidance on when and how to use contrapositive reasoning in Verus. If attempting proof-by-contradiction, the agent must correctly instantiate quantified invariants BEFORE asserting the contradiction hypothesis.

## Key Insights

### 1. Code-State Cascade Dominates System Behavior

This trace demonstrates **Pattern 2** from the dependency prior analysis: when an accepted action commits to a suboptimal proof direction, all downstream actions inherit that degraded baseline, causing cascading failures.

- Position 9 acceptance → 8 downstream failures
- Position 29 acceptance → 4 downstream failures

### 2. Manifestation ≠ Root Cause

The Phase 2 statistical analysis correctly identified `instantiate_forall` as having the highest failure count (14 rejections). However, causal analysis reveals:
- 8 of those failures were caused by `uselemma` at position 9
- 4 of those failures were caused by a different `instantiate_forall` at position 29
- Only position 29 itself represents an `instantiate_forall` prompt issue

This demonstrates the critical importance of causal backtracking - optimizing only the `instantiate_forall` prompt would miss the more fundamental issue in the `uselemma` prompt.

### 3. Router Not at Fault

The `assertion_reasoning_pipeline` router consistently selected `instantiate_forall` for the failing assertion. This was the CORRECT action selection - the problem was in the execution agents' inability to complete the proof, not in the router's choice.

## Comparison to Phase 2 Results

| Phase | Selected Component | Reason |
|-------|-------------------|--------|
| Phase 2 | `instantiate_forall` | Highest failure count (14 rejections) |
| Phase 3 | `uselemma` | Root cause of 8 failures (Segment 1) |
| Phase 3 | `instantiate_forall` | Root cause of 4 failures (Segment 2) |

**Phase 3 reveals that the root causes are DIFFERENT from the manifestation nodes identified in Phase 2.**

## Recommendations for Phase 4

### Priority 1: Optimize `uselemma` Prompt
- Add guidance on completing proof connections after lemma calls
- Include examples showing how to bridge lemma conclusions to proof goals
- Expected impact: Prevent 8+ rejections per trace

### Priority 2: Optimize `instantiate_forall` Prompt
- Add guidance on contrapositive reasoning in Verus
- Clarify when to use proof-by-contradiction vs. direct proof
- Include examples of correct quantifier instantiation for invariants
- Expected impact: Prevent 4+ rejections per trace

### Metric for Success
After prompt optimization, we expect:
- Traces that previously failed at position 9 should complete the proof by position 11
- Traces that previously required position 29's contrapositive should complete with direct proof
- Overall reduction in rejection count from 14 to ≤2 per trace

## Files Generated

1. **sampled_traces_phase_3_1.json**: Traces sampled for each selected subagent
2. **causal_slicing_chain.json**: Causal segments with root cause attribution
3. **root_cause_locations.json**: Final root cause localization by component
4. **phase3_causal_context_extraction_report.md**: This report
