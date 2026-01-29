import os
import asyncio
from typing import Any
from claude_agent_sdk import tool
import json
import re

@tool(
    name="search_context_in_file",
    description="Search for a target string in a file using a character window strategy. Returns a specific number of characters around the match. Can optionally filter results to only include matches within specific sub_agent_calling_N blocks by providing a locations list.",
    input_schema={
        "file_path": str, 
        "target_text": str,
        "window_before": int,  # Characters before match, default 400
        "window_after": int,   # Characters after match, default 400
        "locations": list      # Optional: list of subagent numbers to filter, e.g., [1, 3, 5] means only search in sub_agent_calling_1, sub_agent_calling_3, sub_agent_calling_5
    }
)
async def search_context_in_file(args: dict[str, Any]) -> dict[str, Any]:
    file_path = args.get("file_path")
    target_text = args.get("target_text")
    # Default: 400 chars before and after (roughly 200-300 tokens total)
    window_before = args.get("window_before", 400)
    window_after = args.get("window_after", 400)
    locations = args.get("locations", None)  # e.g., [1, 3, 4, 5, 6]
    
    # Limit window size to prevent excessive output
    window_before = max(0, min(window_before, 2000))
    window_after = max(0, min(window_after, 2000))

    if not file_path or not os.path.exists(file_path):
        return {"content": [{"type": "text", "text": f"Error: File not found: {file_path}"}], "isError": True}

    try:
        # 1. Read entire file content
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # 2. If locations is specified, find the character ranges for each sub_agent_calling_N
        subagent_ranges = {}
        if locations:
            # Find all sub_agent_calling_N patterns and their positions
            # Pattern: "sub_agent_calling_N": { ... }
            pattern = r'"sub_agent_calling_(\d+)"'
            
            for match in re.finditer(pattern, content):
                agent_num = int(match.group(1))
                start_pos = match.start()
                
                # Find the end of this sub_agent block by counting braces
                # Start after the opening brace
                brace_start = content.find('{', match.end())
                if brace_start == -1:
                    continue
                
                brace_count = 1
                pos = brace_start + 1
                while pos < len(content) and brace_count > 0:
                    if content[pos] == '{':
                        brace_count += 1
                    elif content[pos] == '}':
                        brace_count -= 1
                    pos += 1
                
                end_pos = pos
                subagent_ranges[agent_num] = (start_pos, end_pos)
            
            # Filter to only include specified locations
            valid_ranges = [(subagent_ranges[loc][0], subagent_ranges[loc][1], loc) 
                           for loc in locations if loc in subagent_ranges]
            
            if not valid_ranges:
                return {"content": [{"type": "text", "text": f"No matching sub_agent_calling blocks found for locations {locations}"}]}
        
        total_len = len(content)
        all_matches_output = []
        match_count = 0
        current_pos = 0
        
        # 3. Search for all matches
        while True:
            match_index = content.find(target_text, current_pos)
            if match_index == -1:
                break
            
            # 4. If locations is specified, check if this match is within a valid subagent block
            in_valid_location = True
            matched_location = None
            
            if locations:
                in_valid_location = False
                for start, end, loc_num in valid_ranges:
                    if start <= match_index < end:
                        in_valid_location = True
                        matched_location = loc_num
                        break
            
            if in_valid_location:
                match_count += 1
                
                # 5. Calculate slice window
                start_idx = max(0, match_index - window_before)
                end_idx = min(total_len, match_index + len(target_text) + window_after)
                
                # Extract snippet
                snippet = content[start_idx:end_idx]
                
                # 6. Calculate line number for reference
                line_number = content.count('\n', 0, match_index) + 1
                
                # 7. Format output
                clean_snippet = snippet.replace('\n', '↩')
                
                location_info = f" [sub_agent_calling_{matched_location}]" if matched_location else ""
                
                block = (
                    f"=== Match #{match_count} (Approx. Line {line_number}){location_info} ===\n"
                    f"Location: Char index {match_index} to {match_index + len(target_text)}\n"
                    f"Content Context:\n"
                    f"...{clean_snippet}..."
                )
                
                all_matches_output.append(block)
                
                if len(all_matches_output) >= 20:
                    all_matches_output.append("\n(Stopping after 20 matches)")
                    break
            
            # Move to next position
            current_pos = match_index + len(target_text)

        if match_count == 0:
            location_msg = f" within sub_agent_calling {locations}" if locations else ""
            return {"content": [{"type": "text", "text": f"Not found: '{target_text}'{location_msg}"}]}

        location_filter_msg = f" (filtered by locations: {locations})" if locations else ""
        final_output = "\n\n".join(all_matches_output)
        return {
            "content": [{
                "type": "text", 
                "text": f"Found {match_count} matches in '{file_path}'{location_filter_msg}. Showing {window_before} chars before and {window_after} chars after each match:\n\n{final_output}"
            }]
        }

    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}


@tool(
    name="get_trace_structure",
    description="Extract and analyze the structure of a JSON file, recursively breaking down all nested dictionaries and lists. For each value, returns its type and length/size information.",
    input_schema={
        "file_path": str
    }
)
async def get_trace_structure(args: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively analyze JSON structure and return detailed type and size information.
    
    For each element:
    - dict: returns structure of all keys
    - list: returns structure with length and first few element types
    - str: returns type and length
    - numbers: returns type and value
    - bool/null: returns type
    """
    file_path = args.get("file_path")
    
    # Validation
    if not file_path or not os.path.exists(file_path):
        return {
            "content": [{
                "type": "text",
                "text": f"Error: File does not exist or path is empty: {file_path}"
            }],
            "isError": True
        }
    
    try:
        import json
        
        # Read JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        def analyze_structure(obj, path="root", max_depth=50, current_depth=0):
            """Recursively analyze the structure of any JSON object."""
            if current_depth > max_depth:
                return f"<max depth {max_depth} reached>"
            
            obj_type = type(obj).__name__
            
            if obj is None:
                return {"type": "null"}
            
            elif isinstance(obj, bool):
                return {"type": "bool", "value": obj}
            
            elif isinstance(obj, (int, float)):
                return {"type": obj_type, "value": obj}
            
            elif isinstance(obj, str):
                return {
                    "type": "string",
                    "length": len(obj),
                    "preview": obj[:50] + "..." if len(obj) > 50 else obj
                }
            
            elif isinstance(obj, list):
                structure = {
                    "type": "list",
                    "length": len(obj),
                    "elements": []
                }
                
                # Analyze first few elements and unique types
                sampled_indices = []
                if len(obj) > 0:
                    # Sample: first, middle, last elements (up to 5 total)
                    sampled_indices = [0]
                    if len(obj) > 1:
                        sampled_indices.append(len(obj) - 1)
                    if len(obj) > 2:
                        sampled_indices.insert(1, len(obj) // 2)
                    if len(obj) > 5:
                        sampled_indices.insert(1, len(obj) // 4)
                        sampled_indices.insert(-1, 3 * len(obj) // 4)
                    
                    sampled_indices = sorted(set(sampled_indices))[:5]
                
                for idx in sampled_indices:
                    element_structure = analyze_structure(
                        obj[idx], 
                        f"{path}[{idx}]", 
                        max_depth, 
                        current_depth + 1
                    )
                    structure["elements"].append({
                        "index": idx,
                        "structure": element_structure
                    })
                
                return structure
            
            elif isinstance(obj, dict):
                structure = {
                    "type": "dict",
                    "num_keys": len(obj),
                    "keys": {}
                }
                
                for key, value in obj.items():
                    key_path = f"{path}.{key}" if path != "root" else key
                    structure["keys"][key] = analyze_structure(
                        value, 
                        key_path, 
                        max_depth, 
                        current_depth + 1
                    )
                
                return structure
            
            else:
                return {"type": obj_type, "value": str(obj)[:100]}
        
        # Analyze the entire structure
        structure = analyze_structure(data)
        
        # Format as compact JSON string
        import json
        formatted_output = json.dumps(structure, ensure_ascii=False)
        
        return {
            "content": [{
                "type": "text",
                "text": f"Structure of '{file_path}':\n\n{formatted_output}"
            }]
        }
    
    except json.JSONDecodeError as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error: Invalid JSON format in '{file_path}': {str(e)}"
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
