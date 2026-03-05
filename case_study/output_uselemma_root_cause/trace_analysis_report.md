# Trace Analysis Report

**Traces**: 1 | **Success**: 0 (0%) | **Failed**: 1

**Action Nodes**: 6 | **Router Nodes**: 1

## Top Failing Actions

| Action | Rejections | Calls | Reject Rate |
|--------|------------|-------|-------------|
| instantiate_forall | 12 | 14 | 86% |
| add_trigger_assert | 1 | 1 | 100% |
| seqsetmap | 1 | 1 | 100% |

## Action Details

**add_trigger_assert**: 1 calls, 0 accepted (0%), 1 rejected, avg verified=40.0, avg errors=1.0

**instantiate_forall**: 14 calls, 2 accepted (14%), 12 rejected, avg verified=40.0, avg errors=1.0

**postcondition_repair**: 1 calls, 1 accepted (100%), 0 rejected, avg verified=40.0, avg errors=1.0

**reveal_opaque**: 1 calls, 1 accepted (100%), 0 rejected, avg verified=40.0, avg errors=1.0

**seqsetmap**: 1 calls, 0 accepted (0%), 1 rejected, avg verified=40.0, avg errors=1.0

**uselemma**: 1 calls, 1 accepted (100%), 0 rejected, avg verified=40.0, avg errors=1.0

## Router Analysis

**assertion_reasoning_pipeline** (18 calls):
- Selected actions: INSTANTIATE_FORALL(10), REVEAL_OPAQUE(1), ADD_TRIGGER_ASSERT(1), USELEMMA(1), SEQSETMAP(1)

