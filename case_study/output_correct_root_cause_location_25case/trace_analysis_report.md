# VeruSAGE Trace Analysis Report

## Overall Statistics

- Total Traces: 200
- Successful Repairs: 109 (54.5%)
- Failed Repairs: 91 (45.5%)

## Agent Node Statistics

- Total Action Nodes: 28
- Total Router Nodes: 0

## Top Failing Action Nodes

| Node | Rejections | Accept Rate |
|------|------------|-------------|
| postcondition_repair | 348 | 38.84% |
| case_analysis | 317 | 31.53% |
| compute | 129 | 6.52% |
| uselemma | 117 | 38.10% |
| instantiate_forall | 107 | 47.80% |
| seqsetmap | 105 | 8.70% |
| plain_text_repair | 82 | 4.65% |
| induction | 80 | 19.19% |
| extensional_equality | 74 | 38.84% |
| instantiate_exists | 60 | 55.56% |

## Node Performance Details

### add_trigger_assert (action)
- Calls: 31
- Accepted: 1 (3.23%)
- Rejected: 30
- Avg Verified: 15.68
- Avg Errors: 1.13

### arithmetic_overflow_repair (action)
- Calls: 47
- Accepted: 4 (8.51%)
- Rejected: 43
- Avg Verified: 5.38
- Avg Errors: 1.13

### bit_vector_reasoning (action)
- Calls: 30
- Accepted: 18 (60.00%)
- Rejected: 12
- Avg Verified: 12.80
- Avg Errors: 1.83

### bitvassert_repair (action)
- Calls: 22
- Accepted: 19 (86.36%)
- Rejected: 3
- Avg Verified: 18.86
- Avg Errors: 9.95

### case_analysis (action)
- Calls: 463
- Accepted: 146 (31.53%)
- Rejected: 317
- Avg Verified: 14.10
- Avg Errors: 0.69

### compute (action)
- Calls: 138
- Accepted: 9 (6.52%)
- Rejected: 129
- Avg Verified: 5.20
- Avg Errors: 0.59

### decfailend_repair (action)
- Calls: 18
- Accepted: 0 (0.00%)
- Rejected: 18
- Avg Verified: 0.11
- Avg Errors: 1.89

### extensional_equality (action)
- Calls: 121
- Accepted: 47 (38.84%)
- Rejected: 74
- Avg Verified: 15.02
- Avg Errors: 0.69

### fallback_llm_repair (action)
- Calls: 5
- Accepted: 2 (40.00%)
- Rejected: 3
- Avg Verified: 25.40
- Avg Errors: 0.80

### induction (action)
- Calls: 99
- Accepted: 19 (19.19%)
- Rejected: 80
- Avg Verified: 1.83
- Avg Errors: 0.41

### inductive_lemma (action)
- Calls: 26
- Accepted: 5 (19.23%)
- Rejected: 21
- Avg Verified: 2.54
- Avg Errors: 1.08

### instantiate_exists (action)
- Calls: 135
- Accepted: 75 (55.56%)
- Rejected: 60
- Avg Verified: 8.48
- Avg Errors: 0.50

### instantiate_forall (action)
- Calls: 205
- Accepted: 98 (47.80%)
- Rejected: 107
- Avg Verified: 11.96
- Avg Errors: 0.80

### integer_ring (action)
- Calls: 3
- Accepted: 0 (0.00%)
- Rejected: 3
- Avg Verified: 13.33
- Avg Errors: 1.33

### invariant_end_repair (action)
- Calls: 1
- Accepted: 1 (100.00%)
- Rejected: 0
- Avg Verified: 0.00
- Avg Errors: 2.00

### invariant_front_repair (action)
- Calls: 7
- Accepted: 7 (100.00%)
- Rejected: 0
- Avg Verified: 3.86
- Avg Errors: 1.86

### loopinv (action)
- Calls: 50
- Accepted: 22 (44.00%)
- Rejected: 28
- Avg Verified: 1.52
- Avg Errors: 0.52

### loopnodec_repair (action)
- Calls: 9
- Accepted: 9 (100.00%)
- Rejected: 0
- Avg Verified: 1.44
- Avg Errors: 1.56

### nonlinear_arithmetic (action)
- Calls: 71
- Accepted: 15 (21.13%)
- Rejected: 56
- Avg Verified: 15.76
- Avg Errors: 1.44

### plain_text_repair (action)
- Calls: 86
- Accepted: 4 (4.65%)
- Rejected: 82
- Avg Verified: 17.72
- Avg Errors: 1.41

### postcondition_repair (action)
- Calls: 569
- Accepted: 221 (38.84%)
- Rejected: 348
- Avg Verified: 17.14
- Avg Errors: 0.97

### precondition_repair (action)
- Calls: 68
- Accepted: 52 (76.47%)
- Rejected: 16
- Avg Verified: 11.57
- Avg Errors: 0.82

### precondition_veclen_repair (action)
- Calls: 1
- Accepted: 1 (100.00%)
- Rejected: 0
- Avg Verified: 1.00
- Avg Errors: 2.00

### reveal_opaque (action)
- Calls: 25
- Accepted: 17 (68.00%)
- Rejected: 8
- Avg Verified: 13.28
- Avg Errors: 0.64

### reveal_with_fuel (action)
- Calls: 30
- Accepted: 17 (56.67%)
- Rejected: 13
- Avg Verified: 20.57
- Avg Errors: 0.83

### seqsetmap (action)
- Calls: 115
- Accepted: 10 (8.70%)
- Rejected: 105
- Avg Verified: 6.95
- Avg Errors: 0.67

### termination_repair (action)
- Calls: 2
- Accepted: 2 (100.00%)
- Rejected: 0
- Avg Verified: 0.50
- Avg Errors: 1.00

### uselemma (action)
- Calls: 189
- Accepted: 72 (38.10%)
- Rejected: 117
- Avg Verified: 14.07
- Avg Errors: 0.69

