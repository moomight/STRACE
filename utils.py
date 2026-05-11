import os
from typing import Any
from claude_agent_sdk import tool
import json

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TRACE_SUMMARY_FILE = os.path.join(REPO_ROOT, "output", "trace_summaries.json")


@tool(
    name="search_context_in_file",
    description="Search for target_text in a file and return surrounding context (configurable character window). If filter_positions is provided, only return matches that fall inside the corresponding sub_agent_calling_N blocks — this narrows the search scope, it does NOT replace target_text.",
    input_schema={
        "file_path": str, 
        "target_text": str,
        "window_before": int,  # Characters before match, default 400
        "window_after": int,   # Characters after match, default 400
        "filter_positions": list  # Optional: only keep matches inside these sub_agent_calling_N blocks, e.g., [1, 3, 5]
    }
)
async def search_context_in_file(args: dict[str, Any]) -> dict[str, Any]:
    file_path = args.get("file_path")
    target_text = args.get("target_text")
    # Default: 400 chars before and after (roughly 200-300 tokens total)
    window_before = args.get("window_before", 400)
    window_after = args.get("window_after", 400)
    filter_positions = args.get("filter_positions", None)  # e.g., [1, 3, 4, 5, 6]
    
    # Limit window size to prevent excessive output
    window_before = max(0, min(window_before, 2000))
    window_after = max(0, min(window_after, 2000))

    if not file_path or not os.path.exists(file_path):
        return {"content": [{"type": "text", "text": f"Error: File not found: {file_path}"}], "isError": True}
    if target_text == "":
        return {"content": [{"type": "text", "text": "Error: target_text must not be empty."}], "isError": True}

    try:
        # 1. Read entire file content
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        all_matches_output = []
        match_count = 0

        def search_text(search_content: str, matched_location: int | None = None) -> bool:
            nonlocal match_count
            total_len = len(search_content)
            current_pos = 0

            while True:
                match_index = search_content.find(target_text, current_pos)
                if match_index == -1:
                    return False

                match_count += 1
                
                start_idx = max(0, match_index - window_before)
                end_idx = min(total_len, match_index + len(target_text) + window_after)
                
                snippet = search_content[start_idx:end_idx]
                
                line_number = search_content.count('\n', 0, match_index) + 1
                
                clean_snippet = snippet.replace('\n', '↩')
                
                location_info = f" [sub_agent_calling_{matched_location}]" if matched_location is not None else ""
                location_scope = f" within sub_agent_calling_{matched_location}" if matched_location is not None else ""
                line_label = "Block Line" if matched_location is not None else "Line"
                char_label = "Block char index" if matched_location is not None else "Char index"
                
                block = (
                    f"=== Match #{match_count} (Approx. {line_label} {line_number}){location_info} ===\n"
                    f"Location: {char_label} {match_index} to {match_index + len(target_text)}{location_scope}\n"
                    f"Content Context:\n"
                    f"...{clean_snippet}..."
                )
                
                all_matches_output.append(block)
                
                if len(all_matches_output) >= 20:
                    all_matches_output.append("\n(Stopping after 20 matches)")
                    return True

                current_pos = match_index + len(target_text)

        if filter_positions:
            data = json.loads(content)
            if not isinstance(data, dict):
                return {"content": [{"type": "text", "text": "Error: filter_positions requires a top-level JSON object."}], "isError": True}

            filtered_blocks = []
            for loc in filter_positions:
                key = f"sub_agent_calling_{loc}"
                if key in data:
                    filtered_blocks.append((loc, json.dumps(data[key], ensure_ascii=False, indent=2)))

            if not filtered_blocks:
                return {"content": [{"type": "text", "text": f"No matching sub_agent_calling blocks found for filter_positions {filter_positions}"}]}

            for loc, block_content in filtered_blocks:
                if search_text(block_content, loc):
                    break
        else:
            search_text(content)

        if match_count == 0:
            filter_msg = f" within sub_agent_calling {filter_positions}" if filter_positions else ""
            return {"content": [{"type": "text", "text": f"Not found: '{target_text}'{filter_msg}"}]}

        filter_info = f" (filtered by positions: {filter_positions})" if filter_positions else ""
        final_output = "\n\n".join(all_matches_output)
        return {
            "content": [{
                "type": "text", 
                "text": f"Found {match_count} matches in '{file_path}'{filter_info}. Showing {window_before} chars before and {window_after} chars after each match:\n\n{final_output}"
            }]
        }

    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}


@tool(
    name="get_json_structure",
    description="Show the structure of a JSON file by replacing leaf values with their type names (int, string, bool, null, float). Groups dict keys that share the same value structure using fingerprinting, showing one representative and listing the rest. Ideal for understanding unfamiliar JSON formats quickly.",
    input_schema={
        "file_path": str
    }
)
async def get_json_structure(args: dict[str, Any]) -> dict[str, Any]:
    file_path = args.get("file_path")
    
    if not file_path or not os.path.exists(file_path):
        return {"content": [{"type": "text", "text": f"Error: File not found: {file_path}"}], "isError": True}
    
    try:
        import json
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        def get_fingerprint(v, depth=0):
            """Produce a structural fingerprint for grouping."""
            if depth > 4:
                return type(v).__name__
            if v is None: return "null"
            elif isinstance(v, bool): return "bool"
            elif isinstance(v, int): return "int"
            elif isinstance(v, float): return "float"
            elif isinstance(v, str): return "string"
            elif isinstance(v, list):
                if len(v) == 0: return "list(0)[]"
                return f"list({len(v)})[{get_fingerprint(v[0], depth+1)}]"
            elif isinstance(v, dict):
                sorted_keys = sorted(v.keys())
                inner = ", ".join(f"{k}: {get_fingerprint(v[k], depth+1)}" for k in sorted_keys[:12])
                suffix = ", ..." if len(v) > 12 else ""
                return "{" + inner + suffix + "}"
            return type(v).__name__
        
        def to_skeleton(obj, max_depth=20, depth=0):
            """Replace leaf values with type names, group same-structure dict keys."""
            if depth > max_depth:
                return "..."
            if obj is None: return "null"
            elif isinstance(obj, bool): return "bool"
            elif isinstance(obj, int): return "int"
            elif isinstance(obj, float): return "float"
            elif isinstance(obj, str): return "string"
            elif isinstance(obj, list):
                if len(obj) == 0:
                    return f"[] (0 items)"
                # Show skeleton of first element + length
                elem_skeleton = to_skeleton(obj[0], max_depth, depth + 1)
                return {f"[0..{len(obj)-1}] ({len(obj)} items, showing [0])": elem_skeleton}
            elif isinstance(obj, dict):
                if len(obj) == 0:
                    return "{}"
                keys_list = list(obj.keys())
                # Fingerprint all keys
                groups = {}
                for key in keys_list:
                    fp = get_fingerprint(obj[key])
                    if fp not in groups:
                        groups[fp] = []
                    groups[fp].append(key)
                
                result = {}
                for fp, group_keys in groups.items():
                    if len(group_keys) == 1:
                        # Unique structure — show directly
                        k = group_keys[0]
                        result[k] = to_skeleton(obj[k], max_depth, depth + 1)
                    else:
                        # Multiple keys share structure — show representative + list others
                        rep = group_keys[0]
                        if len(group_keys) <= 8:
                            others = group_keys[1:]
                        else:
                            others = group_keys[1:4] + ["..."] + group_keys[-2:]
                        label = f"{rep}  (+ {len(group_keys)-1} similar: {', '.join(str(o) for o in others)})"
                        result[label] = to_skeleton(obj[rep], max_depth, depth + 1)
                return result
            return str(type(obj).__name__)
        
        skeleton = to_skeleton(data)
        formatted = json.dumps(skeleton, ensure_ascii=False, indent=2)
        
        return {
            "content": [{
                "type": "text",
                "text": f"Structure of '{file_path}':\n\n{formatted}"
            }]
        }
    
    except json.JSONDecodeError as e:
        return {"content": [{"type": "text", "text": f"Error: Invalid JSON in '{file_path}': {str(e)}"}], "isError": True}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error reading '{file_path}': {str(e)}"}], "isError": True}


@tool(
    name="read_multiple_line_ranges",
    description="Read multiple line ranges from a file in a single call. More efficient than calling Read multiple times. Supports reading discontinuous line blocks like L28-L52, L79-L103, etc.",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read"
            },
            "line_ranges": {
                "type": "array",
                "description": "List of [start, end] line number pairs (1-based, inclusive)",
                "items": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 2,
                    "maxItems": 2
                }
            }
        },
        "required": ["file_path", "line_ranges"]
    }
)
async def read_multiple_line_ranges(args: dict[str, Any]) -> dict[str, Any]:
    """
    Read multiple line ranges from a file efficiently.
    
    Args:
        file_path: Path to the file
        line_ranges: List of [start_line, end_line] pairs (1-based, inclusive)
                     Example: [[28, 52], [79, 103], [130, 154]]
    
    Returns:
        Content blocks for each line range
    """
    file_path = args.get("file_path")
    line_ranges = args.get("line_ranges", [])
    
    # Validation
    if not file_path or not os.path.exists(file_path):
        return {
            "content": [{
                "type": "text",
                "text": f"Error: File does not exist or path is empty: {file_path}"
            }],
            "isError": True
        }
    
    if not line_ranges:
        return {
            "content": [{
                "type": "text",
                "text": "Error: No line ranges provided. Expected format: [[start, end], [start, end], ...]"
            }],
            "isError": True
        }
    
    # Validate line_ranges format
    if not isinstance(line_ranges, list):
        return {
            "content": [{
                "type": "text",
                "text": f"Error: line_ranges must be a list, got {type(line_ranges).__name__}"
            }],
            "isError": True
        }
    
    for i, range_pair in enumerate(line_ranges):
        if not isinstance(range_pair, list) or len(range_pair) != 2:
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: Each line range must be a list of [start, end]. Invalid at index {i}: {range_pair}"
                }],
                "isError": True
            }
        if not all(isinstance(x, int) for x in range_pair):
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: Line numbers must be integers. Invalid at index {i}: {range_pair}"
                }],
                "isError": True
            }
    
    try:
        # Read entire file once
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        result_blocks = []
        
        # Sort ranges by start line for better readability
        sorted_ranges = sorted(line_ranges, key=lambda x: x[0])
        
        for start_line, end_line in sorted_ranges:
            # Validate range
            if start_line < 1 or end_line < 1:
                result_blocks.append(
                    f"⚠️  Skipped L{start_line}-L{end_line}: Line numbers must be >= 1"
                )
                continue
            
            if start_line > end_line:
                result_blocks.append(
                    f"⚠️  Skipped L{start_line}-L{end_line}: Start line must be <= end line"
                )
                continue
            
            if start_line > total_lines:
                result_blocks.append(
                    f"⚠️  Skipped L{start_line}-L{end_line}: Start line exceeds file length ({total_lines} lines)"
                )
                continue
            
            # Convert to 0-based index and adjust end_line
            start_idx = start_line - 1
            end_idx = min(end_line, total_lines)
            
            # Extract lines
            block_lines = lines[start_idx:end_idx]
            block_content = ''.join(block_lines)
            
            # Format block with header
            block_header = f"=== Lines {start_line}-{end_line} ==="
            result_blocks.append(f"{block_header}\n{block_content}")
        
        # Combine all blocks
        if not result_blocks:
            final_output = "No valid line ranges were processed."
        else:
            final_output = f"File: {file_path}\n\n" + "\n\n".join(result_blocks)
        
        return {
            "content": [{
                "type": "text",
                "text": final_output
            }]
        }
    
    except UnicodeDecodeError:
        return {
            "content": [{
                "type": "text",
                "text": f"Error: Unable to decode file '{file_path}' as UTF-8. File may be binary."
            }],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error reading file '{file_path}': {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="read_trace_positions",
    description="Read specific positions (entries) from a trace JSON file and return their content with smart truncation. Works with any trace format: dict with numbered keys (e.g., 'step_1', 'position_2', 'sub_agent_calling_3') or a top-level list. Positions are 1-based. Long string values are automatically truncated to save cost.",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the trace JSON file"
            },
            "positions": {
                "type": "array",
                "description": "List of position numbers (1-based) to read, e.g. [1, 4, 5]",
                "items": {"type": "integer"}
            },
            "max_string_length": {
                "type": "integer",
                "description": "Maximum characters for any single string value (default: 2000). Longer strings are truncated showing beginning and end.",
                "default": 2000
            }
        },
        "required": ["file_path", "positions"]
    }
)
async def read_trace_positions(args: dict[str, Any]) -> dict[str, Any]:
    """
    Read specific positions from a trace JSON file.
    
    Auto-detects trace format:
    - If top-level is a list: position N → index N-1 (1-based)
    - If top-level is a dict: tries common key patterns like 
      'sub_agent_calling_N', 'step_N', 'position_N', or falls back to 
      the Nth key in insertion order
    
    All string values deeper than top level are truncated to max_string_length.
    """
    file_path = args.get("file_path")
    positions = args.get("positions", [])
    max_len = args.get("max_string_length", 2000)
    
    if not file_path or not os.path.exists(file_path):
        return {
            "content": [{"type": "text", "text": f"Error: File does not exist: {file_path}"}],
            "isError": True
        }
    
    if not positions:
        return {
            "content": [{"type": "text", "text": "Error: No positions provided."}],
            "isError": True
        }
    if max_len < 2:
        return {
            "content": [{"type": "text", "text": "Error: max_string_length must be at least 2."}],
            "isError": True
        }
    
    def truncate_strings(obj, max_len, depth=0):
        """Recursively truncate long strings in a JSON object."""
        if isinstance(obj, str):
            if len(obj) > max_len:
                half = max_len // 2
                return obj[:half] + f"\n... [{len(obj) - max_len} chars truncated] ...\n" + obj[-half:]
            return obj
        elif isinstance(obj, dict):
            return {k: truncate_strings(v, max_len, depth + 1) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [truncate_strings(item, max_len, depth + 1) for item in obj]
        else:
            return obj
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Determine how to map position numbers to entries
        entries = {}  # pos -> (key_label, value)
        
        if isinstance(data, list):
            # List format: position N → index N-1
            total = len(data)
            for pos in positions:
                idx = pos - 1
                if 0 <= idx < total:
                    entries[pos] = (f"index {idx}", data[idx])
                else:
                    entries[pos] = (None, None)
        
        elif isinstance(data, dict):
            # Dict format: try common numbered-key patterns
            keys_list = list(data.keys())
            total = len(keys_list)
            
            # Detect key pattern from existing keys
            key_patterns = [
                lambda n: f"sub_agent_calling_{n}",
                lambda n: f"step_{n}",
                lambda n: f"position_{n}",
                lambda n: f"node_{n}",
                lambda n: f"segment_{n}",
                lambda n: str(n),
            ]
            
            for pos in positions:
                found = False
                # Try each pattern
                for pattern_fn in key_patterns:
                    key = pattern_fn(pos)
                    if key in data:
                        entries[pos] = (key, data[key])
                        found = True
                        break
                
                if not found:
                    # Fallback: use Nth key (1-based)
                    idx = pos - 1
                    if 0 <= idx < total:
                        key = keys_list[idx]
                        entries[pos] = (f"{key} (by order)", data[key])
                    else:
                        entries[pos] = (None, None)
        else:
            return {
                "content": [{"type": "text", "text": f"Error: Top-level JSON is {type(data).__name__}, expected dict or list."}],
                "isError": True
            }
        
        # Format output
        result_blocks = []
        for pos in sorted(positions):
            key_label, value = entries.get(pos, (None, None))
            
            if key_label is None:
                result_blocks.append(f"=== Position {pos} ===\n⚠️ Not found (total entries: {total})")
                continue
            
            # Truncate long strings recursively
            truncated_value = truncate_strings(value, max_len)
            
            # Format as compact JSON
            formatted = json.dumps(truncated_value, ensure_ascii=False, indent=2)
            
            result_blocks.append(f"=== Position {pos} [{key_label}] ===\n{formatted}")
        
        return {
            "content": [{
                "type": "text",
                "text": f"File: {os.path.basename(file_path)} ({total} entries)\n\n" + "\n\n".join(result_blocks)
            }]
        }
    
    except json.JSONDecodeError as e:
        return {
            "content": [{"type": "text", "text": f"Error: Invalid JSON in '{file_path}': {e}"}],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }


@tool(
    name="get_trace_statistics",
    description="Get pre-computed statistics and summaries for all traces. Returns action-level statistics (success/failure rates, error types) and trace summaries without reading full trace content. Much more cost-efficient than reading individual traces.",
    input_schema={
        "summary_file": str  # Path to the pre-computed summary JSON file
    }
)
async def get_trace_statistics(args: dict[str, Any]) -> dict[str, Any]:
    """
    Read pre-computed trace statistics from JSON summary file.
    This avoids expensive full-trace reads.
    """
    summary_file = args.get("summary_file", DEFAULT_TRACE_SUMMARY_FILE)
    
    if not os.path.exists(summary_file):
        return {
            "content": [{
                "type": "text",
                "text": f"Error: Summary file not found: {summary_file}\nPlease run trace_analyzer.py first to generate the summary."
            }],
            "isError": True
        }
    
    try:
        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Format the statistics in a readable way
        output_lines = ["# Trace Statistics Summary\n"]
        
        # Overall summary
        output_lines.append("## Overall Statistics")
        summary = data.get("summary", {})
        total = summary.get("total_traces", 0)
        success = summary.get("success_traces", 0)
        failed = summary.get("failed_traces", 0)
        rejected = summary.get("all_rejected_traces", 0)
        
        output_lines.append(f"- Total Traces: {total}")
        output_lines.append(f"- Success: {success} ({success/total*100:.1f}%)" if total > 0 else "- Success: 0")
        output_lines.append(f"- Failed: {failed} ({failed/total*100:.1f}%)" if total > 0 else "- Failed: 0")
        output_lines.append(f"- All Rejected: {rejected} ({rejected/total*100:.1f}%)\n" if total > 0 else "- All Rejected: 0\n")
        
        # Action statistics
        output_lines.append("## Action-Level Statistics")
        action_stats = data.get("action_statistics", {})
        
        # Sort by total calls
        sorted_actions = sorted(action_stats.items(), key=lambda x: x[1]["total_calls"], reverse=True)
        
        for action_name, stats in sorted_actions:
            output_lines.append(f"\n### {action_name}")
            output_lines.append(f"- Total Calls: {stats['total_calls']}")
            output_lines.append(f"- Success: {stats['success_calls']}")
            output_lines.append(f"- Failed: {stats['failed_calls']}")
            output_lines.append(f"- Rejected: {stats['rejected_calls']}")
            output_lines.append(f"- Success Rate: {stats['success_calls']/stats['total_calls']*100:.1f}%" if stats['total_calls'] > 0 else "- Success Rate: N/A")
            
            if stats['error_types']:
                output_lines.append("- Error Types:")
                for error_type, count in stats['error_types'].items():
                    output_lines.append(f"  - {error_type}: {count}")
        
        # Action chains
        output_lines.append("\n## Most Common Action Chains")
        action_chains = data.get("action_chains", {})
        for chain, count in list(action_chains.items())[:10]:
            output_lines.append(f"- {chain} (x{count})")
        
        # Repeated failures
        output_lines.append("\n## Repeated Failure Patterns")
        repeated = data.get("repeated_failures", [])
        if repeated:
            output_lines.append(f"Found {len(repeated)} cases of consecutive same-action calls")
            
            # Group by action
            from collections import defaultdict
            by_action = defaultdict(list)
            for item in repeated:
                by_action[item["action"]].append(item["file"])
            
            for action, files in by_action.items():
                output_lines.append(f"\n### {action} ({len(files)} occurrences)")
                for file in files[:5]:
                    output_lines.append(f"- {file}")
                if len(files) > 5:
                    output_lines.append(f"- ... and {len(files)-5} more")
        else:
            output_lines.append("No repeated failure patterns detected")
        
        return {
            "content": [{
                "type": "text",
                "text": "\n".join(output_lines)
            }]
        }
    
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error reading summary file: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="get_trace_detail",
    description="Get detailed information about a specific trace from the pre-computed summaries. Returns the trace's action chain, status, error patterns, and agent-level details without reading the full trace content.",
    input_schema={
        "trace_name": str,  # Name of the trace file (e.g., "extra__mod_add_zero-0.json")
        "summary_file": str  # Path to the pre-computed summary JSON file (optional)
    }
)
async def get_trace_detail(args: dict[str, Any]) -> dict[str, Any]:
    """
    Get detailed information about a specific trace from summaries.
    Much cheaper than reading the full trace file.
    """
    trace_name = args.get("trace_name")
    summary_file = args.get("summary_file", DEFAULT_TRACE_SUMMARY_FILE)
    
    if not trace_name:
        return {
            "content": [{
                "type": "text",
                "text": "Error: trace_name is required"
            }],
            "isError": True
        }
    
    if not os.path.exists(summary_file):
        return {
            "content": [{
                "type": "text",
                "text": f"Error: Summary file not found: {summary_file}\nPlease run trace_analyzer.py first."
            }],
            "isError": True
        }
    
    try:
        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Find the trace
        trace_details = data.get("trace_details", [])
        trace_info = None
        
        for trace in trace_details:
            if trace.get("file_name") == trace_name:
                trace_info = trace
                break
        
        if not trace_info:
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: Trace '{trace_name}' not found in summaries"
                }],
                "isError": True
            }
        
        # Format the trace detail
        output_lines = [f"# Trace Detail: {trace_name}\n"]
        
        output_lines.append(f"**Final Status**: {trace_info.get('final_status', 'unknown')}")
        output_lines.append(f"**Total Turns**: {trace_info.get('total_turns', 0)}\n")
        
        # Action chain
        action_chain = trace_info.get("action_chain", [])
        output_lines.append(f"**Action Chain**: {' -> '.join(action_chain)}\n")
        
        # Sub-agent details
        output_lines.append("## Sub-Agent Details")
        sub_agents = trace_info.get("sub_agents", {})
        
        for agent_key in sorted(sub_agents.keys()):
            agent = sub_agents[agent_key]
            output_lines.append(f"\n### {agent_key}")
            output_lines.append(f"- Name: {agent.get('name')}")
            output_lines.append(f"- Turns: {agent.get('turns')}")
            output_lines.append(f"- Accepted: {agent.get('accepted')}")
            output_lines.append(f"- Has Error: {agent.get('has_error')}")
            output_lines.append(f"- Candidates: {agent.get('candidates')}")
            output_lines.append(f"- All Rejected: {agent.get('all_rejected')}")
            
            if agent.get('error_types'):
                output_lines.append(f"- Error Types: {', '.join(agent['error_types'])}")
        
        return {
            "content": [{
                "type": "text",
                "text": "\n".join(output_lines)
            }]
        }
    
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {str(e)}"
            }],
            "isError": True
        }
