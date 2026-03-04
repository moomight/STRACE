import asyncio
import os
from claude_agent_sdk import query, ClaudeAgentOptions, ClaudeSDKClient
from message_formatter import MessageFormatter, Colors
from claude_agent_sdk import create_sdk_mcp_server
from tools import search_context_in_file, get_json_structure, read_multiple_line_ranges, get_trace_statistics, get_trace_detail, read_trace_positions
from claude_agent_sdk import ToolPermissionContext, PermissionResultAllow, PermissionResultDeny, AgentDefinition

mcp_server = create_sdk_mcp_server("poagent-tools", tools=[search_context_in_file, get_json_structure, read_multiple_line_ranges, read_trace_positions])
os.environ["CLAUDE_CODE_STREAM_CLOSE_TIMEOUT"] = "3000000"  # Set timeout to 50 minutes

def read_system_prompt(file_path: str) -> str:
    """Read system prompt from a file."""
    with open(file_path, "r") as f:
        return f.read()


async def can_use_tool_callback(  
    tool_name: str,   
    input_data: dict,   
    context: ToolPermissionContext  
) -> PermissionResultAllow | PermissionResultDeny:  
    accepted_tools = ["search_context_in_file", "read_multiple_line_ranges"]
    user_input = input("Accept the tool usage? (y/n): ")  
    if user_input.lower() == "y" or tool_name in accepted_tools:  
        return PermissionResultAllow()  
    else:  
        return PermissionResultDeny(message="Refused by user.")  


async def main():
    # Initialize the beautiful formatter
    formatter = MessageFormatter()
    formatter.print_header()

    async def wrap_prompt(text):
        yield {"type": "user", "message": {"role": "user", "content": text}}

    try:
        phase1_prompt = read_system_prompt("system_prompt/phase1_Graph-based_Environment_Modeling.md")
        phase2_prompt = read_system_prompt("system_prompt/phase2_Statistical_Bottleneck_Diagnosis.md")
        phase3_prompt = read_system_prompt("system_prompt/phase3_Causal_Context_Extraction.md")

        options = ClaudeAgentOptions(
            mcp_servers={"mcp1": mcp_server},
            allowed_tools=["Write", "Read", "Bash", "Glob", "search_context_in_file", "get_json_structure", "read_multiple_line_ranges", "read_trace_positions"],
            # permission_mode="default",  #["default", "acceptEdits", "plan", "bypassPermissions"]
            permission_mode="bypassPermissions",
            can_use_tool=can_use_tool_callback,
            add_dirs=["/home/v-yingchang/X-agent/"],
            cwd=os.getcwd(),
            agents={
                "Phase1": AgentDefinition(
                    description="Graph-based_Environment_Modeling",
                    prompt=phase1_prompt,
                    tools=["Write", "Read", "Bash", "Glob", "mcp__mcp1__search_context_in_file", "mcp__mcp1__get_json_structure", "mcp__mcp1__read_multiple_line_ranges", "mcp__mcp1__read_trace_positions"],
                ),
                "Phase2": AgentDefinition(
                    description="Statistical_Bottleneck_Diagnosis",
                    prompt=phase2_prompt,
                    tools=["Write", "Read", "Bash", "Glob", "mcp__mcp1__search_context_in_file", "mcp__mcp1__get_json_structure", "mcp__mcp1__read_multiple_line_ranges", "mcp__mcp1__read_trace_positions"],
                ),
                "Phase3": AgentDefinition(
                    description="Causal_Context_Extraction",
                    prompt=phase3_prompt,
                    tools=["Write", "Read", "Bash", "Glob", "mcp__mcp1__search_context_in_file", "mcp__mcp1__get_json_structure", "mcp__mcp1__read_multiple_line_ranges", "mcp__mcp1__read_trace_positions"],
                ),
            },
        )

        async with ClaudeSDKClient(options=options) as client:
            print(f"Phase1: Graph-based Environment Modeling...")
            await client.query(wrap_prompt("@Phase1 Follow the steps in the prompt to model the graph-based environment modeling."))
            async for message in client.receive_response():
                formatter.format_message(message)

            print(f"\n\nPhase2: Statistical Bottleneck Diagnosis...")
            await client.query(wrap_prompt("@Phase2 Follow the steps in the prompt for statistical bottleneck diagnosis."))
            async for message in client.receive_response():
                formatter.format_message(message)

            print(f"Phase3: Causal Context Extraction...")
            await client.query(wrap_prompt("@Phase3 Follow the steps in the prompt for causal context extraction."))
            async for message in client.receive_response():
                formatter.format_message(message)
        
        phase4_prompt = read_system_prompt("system_prompt/phase4_Inductive_Policy_Evolution.md")
        Phase4_options = ClaudeAgentOptions(
            system_prompt=phase4_prompt,
            mcp_servers={"mcp1": mcp_server},
            allowed_tools=["Task", "Write", "Read", "Bash", "Glob", "mcp__mcp1__search_context_in_file", "mcp__mcp1__get_json_structure", "mcp__mcp1__read_multiple_line_ranges", "mcp__mcp1__read_trace_positions"],
            permission_mode="bypassPermissions", # default
            can_use_tool=can_use_tool_callback,
            add_dirs=["/home/v-yingchang/X-agent/"],
            cwd=os.getcwd(),
        )

        print(f"\n\nPhase4: Inductive Policy Evolution...")
        async for message in query(
            prompt=wrap_prompt("Follow the steps in the prompt to do the inductive policy evolution."),
            options=Phase4_options
        ):
            # print("RAW:", message)
            formatter.format_message(message)


    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n\n{Colors.RED}❌ Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())