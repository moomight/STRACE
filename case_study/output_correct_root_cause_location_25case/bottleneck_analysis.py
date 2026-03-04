#!/usr/bin/env python3
"""
Phase 2.2: High-Priority Subagent Selection
Analyzes failure patterns and cascade impact to identify bottleneck components
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

def load_data():
    """Load trace summaries and node metrics"""
    with open('/home/v-yingchang/X-agent/output/trace_summaries.json', 'r') as f:
        summaries = json.load(f)
    return summaries

def analyze_failure_patterns(summaries: List[Dict]) -> Dict:
    """Analyze failure patterns for each component"""

    # Track metrics per node
    node_stats = defaultdict(lambda: {
        'total_calls': 0,
        'accepted': 0,
        'rejected': 0,
        'appears_in_failed_traces': 0,
        'final_failure_count': 0,  # Times node is the final failing node
        'cascade_failures': 0,  # Times node failure leads to trace failure
    })

    # Track transition patterns for cascade analysis
    transitions = defaultdict(lambda: defaultdict(int))

    for trace in summaries:
        is_failed_trace = trace['final_status'] == 'failure'
        final_failed_node = trace['failed_node']

        seen_nodes = set()
        prev_node = None

        for action_str in trace['repair_sequence']:
            node_name, status = action_str.split(':')

            # Update node stats
            stats = node_stats[node_name]
            stats['total_calls'] += 1

            if status == 'accepted':
                stats['accepted'] += 1
            else:
                stats['rejected'] += 1

            if is_failed_trace:
                seen_nodes.add(node_name)

            # Track transitions for cascade analysis
            if prev_node:
                transitions[prev_node][node_name] += 1
            prev_node = node_name

        # Update trace-level metrics
        for node in seen_nodes:
            node_stats[node]['appears_in_failed_traces'] += 1

        if final_failed_node:
            node_stats[final_failed_node]['final_failure_count'] += 1

            # If trace failed, the final failing node caused cascade failure
            if is_failed_trace:
                node_stats[final_failed_node]['cascade_failures'] += 1

    return dict(node_stats), transitions

def compute_cascade_impact(transitions: Dict) -> Dict[str, float]:
    """Compute cascade impact score based on fan-out and downstream dependencies"""

    # Calculate fan-out (number of unique downstream nodes)
    fan_out = {}
    for node, targets in transitions.items():
        fan_out[node] = len(targets)  # Unique downstream nodes

    # Calculate total downstream calls (weighted impact)
    downstream_weight = {}
    for node, targets in transitions.items():
        downstream_weight[node] = sum(targets.values())

    # Normalize and combine scores
    max_fanout = max(fan_out.values()) if fan_out else 1
    max_weight = max(downstream_weight.values()) if downstream_weight else 1

    cascade_scores = {}
    for node in set(list(fan_out.keys()) + list(downstream_weight.keys())):
        fanout_score = fan_out.get(node, 0) / max_fanout
        weight_score = downstream_weight.get(node, 0) / max_weight
        cascade_scores[node] = (fanout_score + weight_score) / 2

    return cascade_scores

def rank_components(node_stats: Dict, cascade_scores: Dict) -> List[Tuple[str, Dict]]:
    """Rank components by failure impact"""

    rankings = []

    for node, stats in node_stats.items():
        # Calculate failure metrics
        rejection_rate = stats['rejected'] / stats['total_calls'] if stats['total_calls'] > 0 else 0
        failure_frequency = stats['appears_in_failed_traces']
        final_failure_rate = stats['final_failure_count'] / stats['total_calls'] if stats['total_calls'] > 0 else 0
        cascade_score = cascade_scores.get(node, 0)

        # Composite score: weighted combination
        # Higher weight on rejection rate and final failures
        composite_score = (
            rejection_rate * 0.3 +
            (failure_frequency / 200) * 0.2 +  # Normalize by total traces
            final_failure_rate * 0.3 +
            cascade_score * 0.2
        )

        rankings.append((node, {
            'stats': stats,
            'rejection_rate': rejection_rate,
            'failure_frequency': failure_frequency,
            'final_failure_rate': final_failure_rate,
            'cascade_score': cascade_score,
            'composite_score': composite_score
        }))

    # Sort by composite score descending
    rankings.sort(key=lambda x: x[1]['composite_score'], reverse=True)

    return rankings

def generate_report(rankings: List[Tuple[str, Dict]], output_path: str):
    """Generate markdown report with top bottleneck components"""

    top_k = 5

    with open(output_path, 'w') as f:
        f.write("# Phase 2.2: High-Priority Subagent Selection\n\n")

        f.write("## Methodology\n\n")
        f.write("Components ranked by composite score:\n")
        f.write("- **Rejection Rate** (30%): Frequency of rejected repairs\n")
        f.write("- **Failure Frequency** (20%): Appearance in failed traces\n")
        f.write("- **Final Failure Rate** (30%): Times as final failing node\n")
        f.write("- **Cascade Score** (20%): Downstream impact (fan-out + weight)\n\n")

        f.write("## Top 5 High-Priority Components\n\n")

        for i, (node, metrics) in enumerate(rankings[:top_k], 1):
            stats = metrics['stats']
            f.write(f"### {i}. {node}\n\n")
            f.write(f"**Composite Score**: {metrics['composite_score']:.4f}\n\n")
            f.write("**Metrics**:\n")
            f.write(f"- Total Calls: {stats['total_calls']}\n")
            f.write(f"- Accepted: {stats['accepted']} ({stats['accepted']/stats['total_calls']*100:.1f}%)\n")
            f.write(f"- Rejected: {stats['rejected']} ({metrics['rejection_rate']*100:.1f}%)\n")
            f.write(f"- Appears in Failed Traces: {metrics['failure_frequency']}\n")
            f.write(f"- Final Failure Count: {stats['final_failure_count']}\n")
            f.write(f"- Final Failure Rate: {metrics['final_failure_rate']*100:.1f}%\n")
            f.write(f"- Cascade Impact Score: {metrics['cascade_score']:.4f}\n\n")

            # Justification
            f.write("**Why This Component**:\n")
            if metrics['rejection_rate'] > 0.6:
                f.write(f"- Very high rejection rate ({metrics['rejection_rate']*100:.1f}%) indicates poor prompt quality\n")
            if metrics['final_failure_rate'] > 0.3:
                f.write(f"- High final failure rate ({metrics['final_failure_rate']*100:.1f}%) shows critical path bottleneck\n")
            if metrics['cascade_score'] > 0.5:
                f.write(f"- High cascade score ({metrics['cascade_score']:.4f}) means failures impact many downstream components\n")
            if stats['total_calls'] > 100:
                f.write(f"- Frequently used ({stats['total_calls']} calls) - optimizing will have broad impact\n")
            f.write("\n")

        f.write("## All Components Ranked\n\n")
        f.write("| Rank | Component | Composite Score | Rejection Rate | Final Failures | Cascade Score |\n")
        f.write("|------|-----------|-----------------|----------------|----------------|---------------|\n")

        for i, (node, metrics) in enumerate(rankings, 1):
            f.write(f"| {i} | {node} | {metrics['composite_score']:.4f} | ")
            f.write(f"{metrics['rejection_rate']*100:.1f}% | ")
            f.write(f"{metrics['stats']['final_failure_count']} | ")
            f.write(f"{metrics['cascade_score']:.4f} |\n")

def main():
    print("Loading trace summaries...")
    summaries = load_data()

    print("Analyzing failure patterns...")
    node_stats, transitions = analyze_failure_patterns(summaries)

    print("Computing cascade impact...")
    cascade_scores = compute_cascade_impact(transitions)

    print("Ranking components...")
    rankings = rank_components(node_stats, cascade_scores)

    print("Generating report...")
    output_path = '/home/v-yingchang/X-agent/output/high_priority_components.md'
    generate_report(rankings, output_path)

    # Save JSON for further analysis
    json_output = '/home/v-yingchang/X-agent/output/component_rankings.json'
    with open(json_output, 'w') as f:
        json.dump([{
            'node': node,
            'metrics': metrics
        } for node, metrics in rankings], f, indent=2)

    print(f"\nSaved report to {output_path}")
    print(f"Saved JSON to {json_output}")

if __name__ == "__main__":
    main()
