# Trace Analysis Report

**Traces**: 1 | **Success**: 0 (0%) | **Failed**: 1

**Action Nodes**: 6 | **Router Nodes**: 1

## Top Failing Actions

| Action | Rejections | Calls | Reject Rate |
|--------|------------|-------|-------------|
| compute | 11 | 11 | 100% |
| nonlinear_arithmetic | 3 | 3 | 100% |
| uselemma | 2 | 2 | 100% |
| case_analysis | 1 | 2 | 50% |

## Action Details

**case_analysis**: 2 calls, 1 accepted (50%), 1 rejected, avg verified=1.0, avg errors=0.5

**compute**: 11 calls, 0 accepted (0%), 11 rejected, avg verified=2.6, avg errors=1.3

**nonlinear_arithmetic**: 3 calls, 0 accepted (0%), 3 rejected, avg verified=3.0, avg errors=1.0

**postcondition_repair**: 1 calls, 1 accepted (100%), 0 rejected, avg verified=2.0, avg errors=1.0

**reveal_opaque**: 1 calls, 1 accepted (100%), 0 rejected, avg verified=2.0, avg errors=1.0

**uselemma**: 2 calls, 0 accepted (0%), 2 rejected, avg verified=0.0, avg errors=0.0

## Router Analysis

**assertion_reasoning_pipeline** (19 calls):
- Selected actions: COMPUTE(10), nonlinear_arithmetic(3), uselemma(2), REVEAL_OPAQUE(1), case_analysis(1), compute(1), CASE_ANALYSIS(1)

