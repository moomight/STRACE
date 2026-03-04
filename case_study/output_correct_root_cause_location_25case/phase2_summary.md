# Phase 2: Statistical Bottleneck Diagnosis - Summary

## 2.1 Statistical Failure Analysis

**Overall System Performance:**
- Total Traces: 200
- Success Rate: 54.5% (109 successful, 91 failed)
- Total Action Nodes: 28
- Total Router Nodes: 0

**Key Findings:**
- System exhibits moderate success rate, indicating room for improvement
- All components are action nodes (executors), no routing decision-makers
- High variance in component performance (0% to 100% acceptance rates)

## 2.2 High-Priority Subagent Selection

### Top 5 Bottleneck Components

**Ranking Methodology:**
- Rejection Rate (30%): Frequency of rejected repairs
- Failure Frequency (20%): Appearance in failed traces
- Final Failure Rate (30%): Times as final failing node
- Cascade Score (20%): Downstream impact (fan-out + weight)

#### 1. **postcondition_repair** (Score: 0.4774)
- **Calls:** 569 (most frequently used)
- **Acceptance Rate:** 38.8%
- **Rejection Rate:** 61.2%
- **Critical Issues:** Very high rejection rate, maximum cascade impact (1.0)
- **Justification:** Entry point for most repair flows with highest downstream dependency. Failures cascade through entire pipeline. Optimizing this component will have broadest impact across all traces.

#### 2. **case_analysis** (Score: 0.4374)
- **Calls:** 463
- **Acceptance Rate:** 31.5%
- **Rejection Rate:** 68.5%
- **Critical Issues:** High rejection rate, high cascade score (0.82)
- **Justification:** Critical for handling branching logic in proofs. 20 final failures (highest) indicate this is a terminal bottleneck. Poor performance blocks many downstream reasoning paths.

#### 3. **compute** (Score: 0.4299)
- **Calls:** 138
- **Acceptance Rate:** 6.5%
- **Rejection Rate:** 93.5% (extremely high)
- **Critical Issues:** Worst performance among frequently-used components
- **Justification:** Handles proof-by-computation for concrete values. 93.5% rejection suggests prompt severely mismatches solver capabilities. 13 final failures show critical path importance.

#### 4. **seqsetmap** (Score: 0.3859)
- **Calls:** 115
- **Acceptance Rate:** 8.7%
- **Rejection Rate:** 91.3%
- **Critical Issues:** Very poor understanding of Verus data structures
- **Justification:** Handles Seq/Set/Map reasoning - fundamental to many proofs. 91.3% rejection indicates major knowledge gap in prompt about Verus collection APIs and axioms.

#### 5. **uselemma** (Score: 0.3365)
- **Calls:** 189
- **Acceptance Rate:** 38.1%
- **Rejection Rate:** 61.9%
- **Critical Issues:** Moderate rejection rate but high cascade score (0.58)
- **Justification:** Invokes existing proof functions - a compositional reasoning step. Failures prevent reuse of established lemmas, forcing redundant proof work downstream.

### Other Notable Components

**High Rejection, Lower Volume:**
- `add_trigger_assert`: 96.8% rejection (31 calls) - trigger pattern understanding poor
- `plain_text_repair`: 95.3% rejection (86 calls) - fallback mechanism failing
- `induction`: 80.8% rejection (99 calls) - inductive proof setup weak

**Better Performance:**
- `bitvassert_repair`: 86.4% acceptance (22 calls)
- `precondition_repair`: 76.5% acceptance (68 calls)
- `reveal_opaque`: 68.0% acceptance (25 calls)

## Recommendations

**Immediate Priorities:**
1. Optimize `postcondition_repair` prompt - entry point with maximum cascade impact
2. Improve `case_analysis` guidance - highest final failure count (20)
3. Redesign `compute` prompt - worst rejection rate (93.5%)
4. Enhance `seqsetmap` with better Verus API knowledge
5. Refine `uselemma` for better compositional reasoning

**Expected Impact:**
- Top 5 components account for 1,484 total calls (57% of all agent invocations)
- Current aggregate acceptance rate: 30.9%
- Target: Increase to 50%+ through prompt optimization
- Projected success rate improvement: 54.5% → 65-70%
