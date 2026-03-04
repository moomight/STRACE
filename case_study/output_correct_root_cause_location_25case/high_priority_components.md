# Phase 2.2: High-Priority Subagent Selection

## Methodology

Components ranked by composite score:
- **Rejection Rate** (30%): Frequency of rejected repairs
- **Failure Frequency** (20%): Appearance in failed traces
- **Final Failure Rate** (30%): Times as final failing node
- **Cascade Score** (20%): Downstream impact (fan-out + weight)

## Top 5 High-Priority Components

### 1. postcondition_repair

**Composite Score**: 0.4774

**Metrics**:
- Total Calls: 569
- Accepted: 221 (38.8%)
- Rejected: 348 (61.2%)
- Appears in Failed Traces: 85
- Final Failure Count: 17
- Final Failure Rate: 3.0%
- Cascade Impact Score: 1.0000

**Why This Component**:
- Very high rejection rate (61.2%) indicates poor prompt quality
- High cascade score (1.0000) means failures impact many downstream components
- Frequently used (569 calls) - optimizing will have broad impact

### 2. case_analysis

**Composite Score**: 0.4374

**Metrics**:
- Total Calls: 463
- Accepted: 146 (31.5%)
- Rejected: 317 (68.5%)
- Appears in Failed Traces: 55
- Final Failure Count: 20
- Final Failure Rate: 4.3%
- Cascade Impact Score: 0.8202

**Why This Component**:
- Very high rejection rate (68.5%) indicates poor prompt quality
- High cascade score (0.8202) means failures impact many downstream components
- Frequently used (463 calls) - optimizing will have broad impact

### 3. compute

**Composite Score**: 0.4299

**Metrics**:
- Total Calls: 138
- Accepted: 9 (6.5%)
- Rejected: 129 (93.5%)
- Appears in Failed Traces: 27
- Final Failure Count: 13
- Final Failure Rate: 9.4%
- Cascade Impact Score: 0.4710

**Why This Component**:
- Very high rejection rate (93.5%) indicates poor prompt quality
- Frequently used (138 calls) - optimizing will have broad impact

### 4. seqsetmap

**Composite Score**: 0.3859

**Metrics**:
- Total Calls: 115
- Accepted: 10 (8.7%)
- Rejected: 105 (91.3%)
- Appears in Failed Traces: 20
- Final Failure Count: 4
- Final Failure Rate: 3.5%
- Cascade Impact Score: 0.4079

**Why This Component**:
- Very high rejection rate (91.3%) indicates poor prompt quality
- Frequently used (115 calls) - optimizing will have broad impact

### 5. add_trigger_assert

**Composite Score**: 0.3831

**Metrics**:
- Total Calls: 31
- Accepted: 1 (3.2%)
- Rejected: 30 (96.8%)
- Appears in Failed Traces: 11
- Final Failure Count: 1
- Final Failure Rate: 3.2%
- Cascade Impact Score: 0.3607

**Why This Component**:
- Very high rejection rate (96.8%) indicates poor prompt quality

## All Components Ranked

| Rank | Component | Composite Score | Rejection Rate | Final Failures | Cascade Score |
|------|-----------|-----------------|----------------|----------------|---------------|
| 1 | postcondition_repair | 0.4774 | 61.2% | 17 | 1.0000 |
| 2 | case_analysis | 0.4374 | 68.5% | 20 | 0.8202 |
| 3 | compute | 0.4299 | 93.5% | 13 | 0.4710 |
| 4 | seqsetmap | 0.3859 | 91.3% | 4 | 0.4079 |
| 5 | add_trigger_assert | 0.3831 | 96.8% | 1 | 0.3607 |
| 6 | plain_text_repair | 0.3553 | 95.3% | 4 | 0.2413 |
| 7 | induction | 0.3423 | 80.8% | 7 | 0.3384 |
| 8 | uselemma | 0.3365 | 61.9% | 6 | 0.5761 |
| 9 | nonlinear_arithmetic | 0.3320 | 78.9% | 2 | 0.3898 |
| 10 | decfailend_repair | 0.3303 | 100.0% | 1 | 0.0631 |
| 11 | arithmetic_overflow_repair | 0.3185 | 91.5% | 2 | 0.1362 |
| 12 | instantiate_forall | 0.3180 | 52.2% | 6 | 0.5980 |
| 13 | extensional_equality | 0.3070 | 61.2% | 3 | 0.4353 |
| 14 | integer_ring | 0.3061 | 100.0% | 0 | 0.0256 |
| 15 | inductive_lemma | 0.3051 | 80.8% | 0 | 0.2838 |
| 16 | instantiate_exists | 0.2395 | 44.4% | 2 | 0.4188 |
| 17 | loopinv | 0.2375 | 56.0% | 2 | 0.2773 |
| 18 | reveal_with_fuel | 0.2067 | 43.3% | 1 | 0.2883 |
| 19 | fallback_llm_repair | 0.2018 | 60.0% | 0 | 0.0989 |
| 20 | bit_vector_reasoning | 0.1755 | 40.0% | 0 | 0.2627 |
| 21 | precondition_repair | 0.1635 | 23.5% | 0 | 0.4145 |
| 22 | reveal_opaque | 0.1548 | 32.0% | 0 | 0.2590 |
| 23 | bitvassert_repair | 0.0636 | 13.6% | 0 | 0.1135 |
| 24 | loopnodec_repair | 0.0380 | 0.0% | 0 | 0.1749 |
| 25 | invariant_front_repair | 0.0249 | 0.0% | 0 | 0.1245 |
| 26 | termination_repair | 0.0071 | 0.0% | 0 | 0.0256 |
| 27 | invariant_end_repair | 0.0049 | 0.0% | 0 | 0.0247 |
| 28 | precondition_veclen_repair | 0.0049 | 0.0% | 0 | 0.0247 |
