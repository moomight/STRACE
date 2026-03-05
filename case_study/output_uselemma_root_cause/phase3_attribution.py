#!/usr/bin/env python3
"""
Phase 3.3 & 3.4: Failure Attribution and Root Cause Localization
"""

import json
from pathlib import Path
from collections import defaultdict

def load_json(filepath):
    """Load JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(filepath, data):
    """Save JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def phase_3_3_failure_attribution():
    """
    Phase 3.3: Failure Attribution

    Analyze causal chains to identify root causes.
    Based on the trace analysis:

    Segment 1 (positions 11, 13, 15, 17, 19, 21, 23, 27):
    - Representative position: 11 (instantiate_forall)
    - Causal chain: [1, 3, 5, 9, 11]
    - Position 1: postcondition_repair (accepted) - added assert
    - Position 3: reveal_opaque (accepted) - revealed extra_mappings
    - Position 5: instantiate_forall (accepted) - instantiated forall with case analysis
    - Position 9: uselemma (accepted) - added vaddr_distinct call
    - Position 11: instantiate_forall (rejected) - tried to instantiate inv_inflight_pmem_no_overlap_inflight_pmem

    ROOT CAUSE ANALYSIS for Segment 1:
    Position 9 (uselemma) added the vaddr_distinct call but did NOT complete the proof for the
    case where both mappings come from extra_mappings. The accepted output at position 9 left
    the proof incomplete - it asserted c1 != c2 but did not use this fact to derive !overlap.
    This degraded baseline forced position 11 and subsequent positions to struggle with completing
    the overlap proof, which requires instantiating inv_inflight_pmem_no_overlap_inflight_pmem
    correctly.

    Segment 2 (positions 31, 33, 35, 37):
    - Representative position: 31 (instantiate_forall)
    - Causal chain: [1, 3, 5, 9, 29, 31]
    - Position 29: instantiate_forall (accepted) - introduced contrapositive reasoning but still incomplete
    - Position 31: instantiate_forall (rejected) - tried different instantiation approach

    ROOT CAUSE ANALYSIS for Segment 2:
    Position 29 (instantiate_forall) accepted a change that introduced contrapositive reasoning
    but created a more complex proof structure without actually completing it. The accepted output
    at position 29 committed to a proof approach (contrapositive) that made the proof harder,
    degrading the baseline further.
    """

    print("\n=== Phase 3.3: Failure Attribution ===")

    base_dir = Path('/home/v-yingchang/X-agent')
    output_dir = base_dir / 'output'

    causal_slicing = load_json(output_dir / 'causal_slicing_chain.json')

    # Analyze and attribute failures
    trace_file = 'NR__impl_u__os_refinement__no_overlaps_pmem_applied_mappings-20251128-0.json'

    results = {}

    # Segment 1 attribution
    # Looking at the causal chain: [1, 3, 5, 9, 11]
    # Position 1: postcondition_repair (accepted) - basic postcondition assertion
    # Position 3: reveal_opaque (accepted) - revealed definition
    # Position 5: instantiate_forall (accepted) - case analysis structure
    # Position 9: uselemma (accepted) - added vaddr_distinct but incomplete proof
    # Position 11: instantiate_forall (rejected) - tries to fix position 9's incomplete proof
    #
    # ROOT CAUSE: Position 9 (uselemma)
    # The uselemma agent added vaddr_distinct(c, s) call but left the proof incomplete.
    # It showed c1 != c2 but did not connect this to the overlap goal using
    # inv_inflight_pmem_no_overlap_inflight_pmem. This created a degraded baseline.

    segment_1 = {
        "segment_positions": [11, 13, 15, 17, 19, 21, 23, 27],
        "representative_manifestation_node": 11,
        "causal_chain": [1, 3, 5, 9, 11],
        "root_cause_subagent": "uselemma",
        "root_cause_position": 9,
        "reason": "Added vaddr_distinct lemma call but did not complete the proof bridge to show how c1 != c2 implies !overlap using inv_inflight_pmem_no_overlap_inflight_pmem, leaving downstream positions to struggle with the incomplete proof structure"
    }

    # Segment 2 attribution
    # Causal chain: [1, 3, 5, 9, 29, 31]
    # Position 29: instantiate_forall (accepted) - introduced contrapositive but incomplete
    # Position 31: instantiate_forall (rejected) - tries different approach
    #
    # ROOT CAUSE: Position 29 (instantiate_forall)
    # This position introduced contrapositive reasoning (assert c1 == c2 to derive contradiction)
    # but implemented it incorrectly, creating an even more complex and broken proof structure.
    # The accepted output degraded the baseline further.

    segment_2 = {
        "segment_positions": [31, 33, 35, 37],
        "representative_manifestation_node": 31,
        "causal_chain": [1, 3, 5, 9, 29, 31],
        "root_cause_subagent": "instantiate_forall",
        "root_cause_position": 29,
        "reason": "Introduced contrapositive reasoning structure (assert c1 == c2 to derive contradiction) but implemented it incorrectly with wrong quantifier instantiation, creating a more complex and broken proof that degraded the baseline"
    }

    results[trace_file] = [segment_1, segment_2]

    save_json(output_dir / 'causal_slicing_chain.json', {trace_file: {
        'target_subagent': 'instantiate_forall',
        'segments': [segment_1, segment_2]
    }})

    print(f"Segment 1 root cause: {segment_1['root_cause_subagent']} at position {segment_1['root_cause_position']}")
    print(f"  Reason: {segment_1['reason']}")
    print(f"Segment 2 root cause: {segment_2['root_cause_subagent']} at position {segment_2['root_cause_position']}")
    print(f"  Reason: {segment_2['reason']}")

    return results

def phase_3_4_root_cause_localization(attribution_results):
    """
    Phase 3.4: Root Cause Localization

    Aggregate attribution results by root cause component.
    """
    print("\n=== Phase 3.4: Root Cause Localization ===")

    base_dir = Path('/home/v-yingchang/X-agent')
    output_dir = base_dir / 'output'

    # Load causal slicing results
    causal_slicing = load_json(output_dir / 'causal_slicing_chain.json')

    root_cause_locations = defaultdict(list)

    trace_file = 'NR__impl_u__os_refinement__no_overlaps_pmem_applied_mappings-20251128-0.json'
    segments = causal_slicing[trace_file]['segments']

    for segment in segments:
        subagent = segment['root_cause_subagent']
        location = [segment['root_cause_position']]
        reason = segment['reason']

        root_cause_locations[subagent].append({
            'trace': trace_file,
            'location': location,
            'reason': reason
        })

    # Convert to regular dict for JSON serialization
    root_cause_locations = dict(root_cause_locations)

    save_json(output_dir / 'root_cause_locations.json', root_cause_locations)

    print(f"Root cause components identified: {list(root_cause_locations.keys())}")
    for subagent, entries in root_cause_locations.items():
        print(f"\n{subagent}:")
        for entry in entries:
            print(f"  Trace: {entry['trace']}")
            print(f"  Location: {entry['location']}")
            print(f"  Reason: {entry['reason'][:100]}...")

    return root_cause_locations

def main():
    """Main execution."""

    # Phase 3.3: Failure Attribution
    attribution_results = phase_3_3_failure_attribution()

    # Phase 3.4: Root Cause Localization
    root_cause_locations = phase_3_4_root_cause_localization(attribution_results)

    print("\n=== Phase 3 Complete ===")
    print(f"Results saved to /home/v-yingchang/X-agent/output/")
    print(f"- causal_slicing_chain.json (updated with root cause attribution)")
    print(f"- root_cause_locations.json (final root cause localization)")

if __name__ == '__main__':
    main()
