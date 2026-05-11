import asyncio
import os
from claude_agent_sdk import query, ClaudeAgentOptions, ClaudeSDKClient
from message_formatter import MessageFormatter, Colors
from claude_agent_sdk import create_sdk_mcp_server
from tools import search_context_in_file, get_json_structure, read_multiple_line_ranges, get_trace_statistics, get_trace_detail, read_trace_positions
from claude_agent_sdk import ToolPermissionContext, PermissionResultAllow, PermissionResultDeny
from claude_agent_sdk.types import HookMatcher, SyncHookJSONOutput

mcp_server = create_sdk_mcp_server("poagent-tools", tools=[search_context_in_file, get_json_structure, read_multiple_line_ranges, read_trace_positions])
os.environ["CLAUDE_CODE_STREAM_CLOSE_TIMEOUT"] = "3000000"  # Set timeout to 50 minutes

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def read_system_prompt(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()


async def can_use_tool_callback(  
    tool_name: str,   
    input_data: dict,   
    context: ToolPermissionContext  
) -> PermissionResultAllow | PermissionResultDeny:  
    accepted_tools = {
        "search_context_in_file",
        "get_json_structure",
        "read_multiple_line_ranges",
        "read_trace_positions",
        "mcp__mcp1__search_context_in_file",
        "mcp__mcp1__get_json_structure",
        "mcp__mcp1__read_multiple_line_ranges",
        "mcp__mcp1__read_trace_positions",
    }
    if tool_name in accepted_tools:
        return PermissionResultAllow()
    user_input = input("Accept the tool usage? (y/n): ")  
    if user_input.lower() == "y":  
        return PermissionResultAllow()  
    else:  
        return PermissionResultDeny(message="Refused by user.")  


# PreCompact hook: save important info when compacting
async def on_pre_compact(input_data, tool_use_id, context):
    return SyncHookJSONOutput(
        continue_=True,
        reason="When compacting, you MUST preserve: 1) All analysis results and conclusions from previous phases. 2) All file paths that were created or referenced. 3) Key findings, statistics, and data structures. 4) The current phase context and objectives.",
    )


async def main():
    formatter = MessageFormatter()
    formatter.print_header()

    async def wrap_prompt(text):
        yield {"type": "user", "message": {"role": "user", "content": text}}

    try:
        phase1_prompt = read_system_prompt(os.path.join(SCRIPT_DIR, "system_prompt/phase1_Graph-based_Environment_Modeling.md"))
        phase2_prompt = read_system_prompt(os.path.join(SCRIPT_DIR, "system_prompt/phase2_Statistical_Bottleneck_Diagnosis.md"))
        phase3_prompt = read_system_prompt(os.path.join(SCRIPT_DIR, "system_prompt/phase3_Causal_Context_Extraction.md"))

        options = ClaudeAgentOptions(
            mcp_servers={"mcp1": mcp_server},
            # `allowed_tools` means pre-approved, not just visible. For stricter permissions,
            # put tools here under `tools=[...]` instead and approve calls in `can_use_tool_callback`.
            allowed_tools=["Write", "Read", "Bash", "Glob", "mcp__mcp1__search_context_in_file", "mcp__mcp1__get_json_structure", "mcp__mcp1__read_multiple_line_ranges", "mcp__mcp1__read_trace_positions"],
            # tools=["Write", "Read", "Bash", "Glob", "mcp__mcp1__search_context_in_file", "mcp__mcp1__get_json_structure", "mcp__mcp1__read_multiple_line_ranges", "mcp__mcp1__read_trace_positions"],
            permission_mode="default", #["default", "acceptEdits", "plan", "bypassPermissions"]
            can_use_tool=can_use_tool_callback,
            add_dirs=["/home/v-yingchang/X-agent/"],
            cwd=os.getcwd(),
            hooks={
                "PreCompact": [HookMatcher(hooks=[on_pre_compact])],
            },
        )

        async with ClaudeSDKClient(options=options) as client:
            # Phase 1
            print(f"Phase1: Graph-based Environment Modeling...")
            await client.query(wrap_prompt(phase1_prompt + "\n\nExecute the above steps now."))
            async for message in client.receive_response():
                formatter.format_message(message)

            # Compact between Phase 1 and 2
            print(f"\n\nCompacting after Phase1...")
            await client.query(wrap_prompt("/compact Preserve all Phase1 results, file paths, analysis outputs, and key findings."))
            async for message in client.receive_response():
                pass

            # Phase 2
            print(f"\n\nPhase2: Statistical Bottleneck Diagnosis...")
            await client.query(wrap_prompt(phase2_prompt + "\n\nExecute the above steps now."))
            async for message in client.receive_response():
                formatter.format_message(message)

            # Compact between Phase 2 and 3
            print(f"\n\nCompacting after Phase2...")
            await client.query(wrap_prompt("/compact Preserve all Phase1 and Phase2 results, file paths, and key findings."))
            async for message in client.receive_response():
                pass

            # Phase 3
            print(f"\n\nPhase3: Causal Context Extraction...")
            await client.query(wrap_prompt(phase3_prompt + "\n\nExecute the above steps now."))
            async for message in client.receive_response():
                formatter.format_message(message)

        # Phase 4 - separate session, not sharing the previous session's context
        phase4_prompt = read_system_prompt(os.path.join(SCRIPT_DIR, "system_prompt/phase4_Inductive_Policy_Evolution.md"))
        Phase4_options = ClaudeAgentOptions(
            system_prompt=phase4_prompt,
            mcp_servers={"mcp1": mcp_server},
            allowed_tools=["Task", "Write", "Read", "Bash", "Glob", "mcp__mcp1__search_context_in_file", "mcp__mcp1__get_json_structure", "mcp__mcp1__read_multiple_line_ranges", "mcp__mcp1__read_trace_positions"],
            permission_mode="default",
            can_use_tool=can_use_tool_callback,
            add_dirs=["/home/v-yingchang/X-agent/"],
            cwd=os.getcwd(),
        )

        print(f"\n\nPhase4: Inductive Policy Evolution...")
        async for message in query(
            prompt=wrap_prompt("Follow the steps in the prompt to do the inductive policy evolution."),
            options=Phase4_options
        ):
            formatter.format_message(message)

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n\n{Colors.RED}❌ Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
