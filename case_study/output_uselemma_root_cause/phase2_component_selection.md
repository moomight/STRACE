# Phase 2.2: High-Priority Component Selection

## Selected Components (Top 5)

Based on statistical analysis of failure patterns, cascade impact, and pipeline position:

### 1. **assertion_reasoning_pipeline**
**Priority Score: 66.076**
- **Justification**: Central decision-maker with 5 downstream dependents. Appears 18 times with 100% failure rate. Acts as hub connecting all repair strategies. Optimizing this component's prompts will have the highest system-wide impact.
- **Role**: Decision-maker (chooses repair strategies)
- **Cascade Impact**: 109.459 (highest - upstream position with wide fan-out)

### 2. **instantiate_forall**
**Priority Score: 15.805**
- **Justification**: Most frequently invoked repair executor (14 calls, 100% failures). Tight loop with assertion_reasoning_pipeline (14 bidirectional transitions). High failure volume indicates prompt may not be guiding the instantiation strategy effectively.
- **Role**: Executor (performs forall quantifier instantiation)
- **Cascade Impact**: 25.676

### 3. **postcondition_repair**
**Priority Score: 2.2**
- **Justification**: Entry-point agent (position 1.0). As the upstream initiator, failures here cascade through entire pipeline. Despite single call, its initial decision quality affects all downstream work.
- **Role**: Decision-maker (initial repair categorization)
- **Cascade Impact**: 3.0

### 4. **reveal_opaque**
**Priority Score: 2.135**
- **Justification**: Early pipeline component (position 3.0) with upstream influence. Failures in opacity revelation can block downstream reasoning.
- **Role**: Executor (reveals opaque definitions)
- **Cascade Impact**: 2.892

### 5. **add_trigger_assert**
**Priority Score: 2.005**
- **Justification**: Mid-pipeline executor (position 7.0) with moderate cascade potential. Trigger hint quality affects SMT solver guidance.
- **Role**: Executor (adds SMT triggers)
- **Cascade Impact**: 2.676

## Pipeline Architecture Insights

**Execution Pattern**: The dominant loop is `assertion_reasoning_pipeline ↔ instantiate_forall` (27 total transitions), indicating the system repeatedly attempts forall instantiation without convergence.

**Dependency Map**:
```
postcondition_repair → assertion_reasoning_pipeline → {
    reveal_opaque,
    instantiate_forall (primary),
    add_trigger_assert,
    uselemma,
    seqsetmap
}
```

## Optimization Strategy

Focus on the top 3 components for maximum ROI:
1. **assertion_reasoning_pipeline**: Improve strategy selection logic
2. **instantiate_forall**: Enhance term selection guidance
3. **postcondition_repair**: Better initial problem classification

These three account for 89% of total invocations and represent the critical path from problem intake through primary repair loop.
