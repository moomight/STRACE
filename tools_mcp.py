import os
import re
import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("strace-tools")


@mcp.tool()
async def search_context_in_file(
    file_path: str,
    target_text: str,
    window_before: int = 400,
    window_after: int = 400,
    filter_positions: list[int] | None = None,
) -> str:
    """Search for target_text in a file and return surrounding context (configurable character window).
    If filter_positions is provided, only return matches that fall inside the corresponding
    sub_agent_calling_N blocks — this narrows the search scope, it does NOT replace target_text."""

    window_before = max(0, min(window_before, 2000))
    window_after = max(0, min(window_after, 2000))

    if not file_path or not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # If filter_positions is specified, find the character ranges for each sub_agent_calling_N
    subagent_ranges: dict[int, tuple[int, int]] = {}
    valid_ranges: list[tuple[int, int, int]] = []
    if filter_positions:
        pattern = r'"sub_agent_calling_(\d+)"'
        for match in re.finditer(pattern, content):
            agent_num = int(match.group(1))
            start_pos = match.start()
            brace_start = content.find("{", match.end())
            if brace_start == -1:
                continue
            brace_count = 1
            pos = brace_start + 1
            while pos < len(content) and brace_count > 0:
                if content[pos] == "{":
                    brace_count += 1
                elif content[pos] == "}":
                    brace_count -= 1
                pos += 1
            subagent_ranges[agent_num] = (start_pos, pos)

        valid_ranges = [
            (subagent_ranges[loc][0], subagent_ranges[loc][1], loc)
            for loc in filter_positions
            if loc in subagent_ranges
        ]
        if not valid_ranges:
            return f"No matching sub_agent_calling blocks found for filter_positions {filter_positions}"

    total_len = len(content)
    all_matches_output: list[str] = []
    match_count = 0
    current_pos = 0

    while True:
        match_index = content.find(target_text, current_pos)
        if match_index == -1:
            break

        in_valid_location = True
        matched_location = None
        if filter_positions:
            in_valid_location = False
            for start, end, loc_num in valid_ranges:
                if start <= match_index < end:
                    in_valid_location = True
                    matched_location = loc_num
                    break

        if in_valid_location:
            match_count += 1
            start_idx = max(0, match_index - window_before)
            end_idx = min(total_len, match_index + len(target_text) + window_after)
            snippet = content[start_idx:end_idx]
            line_number = content.count("\n", 0, match_index) + 1
            clean_snippet = snippet.replace("\n", "↩")
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

        current_pos = match_index + len(target_text)

    if match_count == 0:
        filter_msg = f" within sub_agent_calling {filter_positions}" if filter_positions else ""
        return f"Not found: '{target_text}'{filter_msg}"

    filter_info = f" (filtered by positions: {filter_positions})" if filter_positions else ""
    final_output = "\n\n".join(all_matches_output)
    return f"Found {match_count} matches in '{file_path}'{filter_info}. Showing {window_before} chars before and {window_after} chars after each match:\n\n{final_output}"


@mcp.tool()
async def get_json_structure(file_path: str) -> str:
    """Show the structure of a JSON file by replacing leaf values with their type names
    (int, string, bool, null, float). Groups dict keys that share the same value structure
    using fingerprinting, showing one representative and listing the rest.
    Ideal for understanding unfamiliar JSON formats quickly."""

    if not file_path or not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    def get_fingerprint(v: object, depth: int = 0) -> str:
        if depth > 4:
            return type(v).__name__
        if v is None:
            return "null"
        elif isinstance(v, bool):
            return "bool"
        elif isinstance(v, int):
            return "int"
        elif isinstance(v, float):
            return "float"
        elif isinstance(v, str):
            return "string"
        elif isinstance(v, list):
            if len(v) == 0:
                return "list(0)[]"
            return f"list({len(v)})[{get_fingerprint(v[0], depth + 1)}]"
        elif isinstance(v, dict):
            sorted_keys = sorted(v.keys())
            inner = ", ".join(f"{k}: {get_fingerprint(v[k], depth + 1)}" for k in sorted_keys[:12])
            suffix = ", ..." if len(v) > 12 else ""
            return "{" + inner + suffix + "}"
        return type(v).__name__

    def to_skeleton(obj: object, max_depth: int = 20, depth: int = 0) -> object:
        if depth > max_depth:
            return "..."
        if obj is None:
            return "null"
        elif isinstance(obj, bool):
            return "bool"
        elif isinstance(obj, int):
            return "int"
        elif isinstance(obj, float):
            return "float"
        elif isinstance(obj, str):
            return "string"
        elif isinstance(obj, list):
            if len(obj) == 0:
                return "[] (0 items)"
            elem_skeleton = to_skeleton(obj[0], max_depth, depth + 1)
            return {f"[0..{len(obj)-1}] ({len(obj)} items, showing [0])": elem_skeleton}
        elif isinstance(obj, dict):
            if len(obj) == 0:
                return "{}"
            keys_list = list(obj.keys())
            groups: dict[str, list[str]] = {}
            for key in keys_list:
                fp = get_fingerprint(obj[key])
                groups.setdefault(fp, []).append(key)
            result = {}
            for fp, group_keys in groups.items():
                if len(group_keys) == 1:
                    k = group_keys[0]
                    result[k] = to_skeleton(obj[k], max_depth, depth + 1)
                else:
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
    return f"Structure of '{file_path}':\n\n{formatted}"


def _truncate_strings(obj: object, max_len: int) -> object:
    """Recursively truncate long strings in a JSON object."""
    if isinstance(obj, str):
        if len(obj) > max_len:
            half = max_len // 2
            return obj[:half] + f"\n... [{len(obj) - max_len} chars truncated] ...\n" + obj[-half:]
        return obj
    elif isinstance(obj, dict):
        return {k: _truncate_strings(v, max_len) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_truncate_strings(item, max_len) for item in obj]
    return obj


@mcp.tool()
async def read_trace_positions(
    file_path: str,
    positions: list[int],
    max_string_length: int = 2000,
) -> str:
    """Read specific positions (entries) from a trace JSON file and return their content
    with smart truncation. Works with any trace format: dict with numbered keys
    (e.g., 'step_1', 'position_2', 'sub_agent_calling_3') or a top-level list.
    Positions are 1-based. Long string values are automatically truncated to save cost."""

    if not file_path or not os.path.exists(file_path):
        raise ValueError(f"File does not exist: {file_path}")
    if not positions:
        raise ValueError("No positions provided.")

    max_len = max_string_length

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries: dict[int, tuple[str | None, object]] = {}

    if isinstance(data, list):
        total = len(data)
        for pos in positions:
            idx = pos - 1
            if 0 <= idx < total:
                entries[pos] = (f"index {idx}", data[idx])
            else:
                entries[pos] = (None, None)

    elif isinstance(data, dict):
        keys_list = list(data.keys())
        total = len(keys_list)
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
            for pattern_fn in key_patterns:
                key = pattern_fn(pos)
                if key in data:
                    entries[pos] = (key, data[key])
                    found = True
                    break
            if not found:
                idx = pos - 1
                if 0 <= idx < total:
                    key = keys_list[idx]
                    entries[pos] = (f"{key} (by order)", data[key])
                else:
                    entries[pos] = (None, None)
    else:
        raise ValueError(f"Top-level JSON is {type(data).__name__}, expected dict or list.")

    result_blocks: list[str] = []
    for pos in sorted(positions):
        key_label, value = entries.get(pos, (None, None))
        if value is None:
            result_blocks.append(f"=== Position {pos} ===\n⚠️ Not found (total entries: {total})")
            continue
        truncated_value = _truncate_strings(value, max_len)
        formatted = json.dumps(truncated_value, ensure_ascii=False, indent=2)
        result_blocks.append(f"=== Position {pos} [{key_label}] ===\n{formatted}")

    return f"File: {os.path.basename(file_path)} ({total} entries)\n\n" + "\n\n".join(result_blocks)


if __name__ == "__main__":
    mcp.run(transport="stdio")
