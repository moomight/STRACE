#!/usr/bin/env python3
"""
Phase 3: Causal Context Extraction
Analyzes traces to identify root causes of failures through causal backtracking.
"""

import json
import sys
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

def extract_execution_sequence(trace_summary):
    """Extract execution sequence with positions and acceptance status."""
    sequence = []
    repair_seq = trace_summary['repair_sequence']

    position = 1
    for i, entry in enumerate(repair_seq):
        parts = entry.split(':')
        if len(parts) == 2:
            name, status = parts
            sequence.append({
                'position': position,
                'name': name,
                'status': status,
                'is_state_changing': status == 'accepted'
            })
            position += 1

    return sequence

def identify_state_changing_positions(sequence):
    """Identify positions that changed state (accepted nodes)."""
    return [item for item in sequence if item['is_state_changing']]

def build_causal_segments(sequence, target_subagent):
    """Build causal segments for target subagent."""
    segments = []
    current_segment_positions = []
    last_state_change_positions = []

    # Track all state-changing positions seen so far
    for item in sequence:
        if item['is_state_changing']:
            last_state_change_positions.append(item['position'])
            # Start new segment when state changes
            if current_segment_positions:
                # Previous segment ends here
                representative = current_segment_positions[0]
                causal_chain = [p for p in last_state_change_positions[:-1]] + [representative]
                segments.append({
                    'segment_positions': current_segment_positions[:],
                    'representative_manifestation_node': representative,
                    'causal_chain': causal_chain
                })
                current_segment_positions = []
        elif item['name'] == target_subagent:
            # Non-state-changing position of target subagent
            current_segment_positions.append(item['position'])

    # Handle last segment if exists
    if current_segment_positions:
        representative = current_segment_positions[0]
        causal_chain = last_state_change_positions + [representative]
        segments.append({
            'segment_positions': current_segment_positions[:],
            'representative_manifestation_node': representative,
            'causal_chain': causal_chain
        })

    return segments

def phase_3_1_sample_traces(high_priority_file, trace_summaries_file, output_file):
    """Phase 3.1: Sample representative traces for each selected subagent."""
    print("\n=== Phase 3.1: Representative Traces Sampling ===")

    high_priority = load_json(high_priority_file)
    trace_summaries = load_json(trace_summaries_file)

    # Get selected subagents
    selected_subagents = high_priority['components']
    print(f"Selected subagents: {selected_subagents}")

    # For this system, we only have 1 trace, so we'll use it for instantiate_forall
    sampled_traces = {}
    for subagent in selected_subagents:
        # Check if this subagent appears in any trace
        for summary in trace_summaries:
            trace_file = summary['trace_file']
            repair_seq = summary['repair_sequence']

            # Check if subagent appears and has failures
            subagent_appears = any(subagent in entry for entry in repair_seq)

            if subagent_appears:
                if subagent not in sampled_traces:
                    sampled_traces[subagent] = []
                if trace_file not in sampled_traces[subagent]:
                    sampled_traces[subagent].append(trace_file)

    print(f"Sampled traces: {sampled_traces}")
    save_json(output_file, sampled_traces)
    return sampled_traces

def phase_3_2_causal_slicing(sampled_traces_file, trace_summaries_file, output_file):
    """Phase 3.2: Backward causal slicing."""
    print("\n=== Phase 3.2: Backward Causal Slicing ===")

    sampled_traces = load_json(sampled_traces_file)
    trace_summaries = load_json(trace_summaries_file)

    # Build trace summary lookup
    trace_lookup = {s['trace_file']: s for s in trace_summaries}

    causal_slicing_results = {}

    for target_subagent, trace_files in sampled_traces.items():
        for trace_file in trace_files:
            if trace_file not in trace_lookup:
                continue

            summary = trace_lookup[trace_file]
            sequence = extract_execution_sequence(summary)

            print(f"\nProcessing: {trace_file} for {target_subagent}")
            print(f"Total positions: {len(sequence)}")

            # Build causal segments
            segments = build_causal_segments(sequence, target_subagent)

            print(f"Found {len(segments)} causal segments")

            if segments:
                causal_slicing_results[trace_file] = {
                    'target_subagent': target_subagent,
                    'segments': segments
                }

    save_json(output_file, causal_slicing_results)
    return causal_slicing_results

def main():
    """Main execution."""
    base_dir = Path('/home/v-yingchang/X-agent')
    output_dir = base_dir / 'output'

    # Phase 3.1: Sample traces
    sampled_traces = phase_3_1_sample_traces(
        output_dir / 'high_priority_components.json',
        output_dir / 'trace_summaries.json',
        output_dir / 'sampled_traces_phase_3_1.json'
    )

    # Phase 3.2: Causal slicing
    causal_slicing = phase_3_2_causal_slicing(
        output_dir / 'sampled_traces_phase_3_1.json',
        output_dir / 'trace_summaries.json',
        output_dir / 'causal_slicing_chain.json'
    )

    print("\n=== Phase 3.1 & 3.2 Complete ===")
    print(f"Results saved to {output_dir}")

if __name__ == '__main__':
    main()
