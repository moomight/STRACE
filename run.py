import asyncio
import os
from claude_agent_sdk import query, ClaudeAgentOptions, ClaudeSDKClient
from message_formatter import MessageFormatter, Colors
from claude_agent_sdk import create_sdk_mcp_server

from tools import search_context_in_file, get_trace_structure, read_multiple_line_ranges
from claude_agent_sdk import ToolPermissionContext, PermissionResultAllow, PermissionResultDeny, AgentDefinition

mcp_server = create_sdk_mcp_server("poagent-tools", tools=[search_context_in_file, get_trace_structure, read_multiple_line_ranges])
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
        step1_prompt = read_system_prompt("system_prompt/Step1_Automated_Diagnostic_Profiling.md")
        step2_prompt = read_system_prompt("system_prompt/Step2_Structural_Bottleneck_localization.md")

        options = ClaudeAgentOptions(
            mcp_servers={"mcp1": mcp_server},
            allowed_tools=["Write", "Read", "Bash", "Glob", "search_context_in_file", "get_trace_structure", "read_multiple_line_ranges"],
            permission_mode="default",  #["default", "acceptEdits", "plan", "bypassPermissions"]
            # permission_mode="bypassPermissions",
            can_use_tool=can_use_tool_callback,
            cwd=os.getcwd(),
            agents={
                "Step1": AgentDefinition(
                    description="Automated_Diagnostic_Profiling",
                    prompt=step1_prompt,
                    tools=["Write", "Read", "Bash", "Glob", "mcp__mcp1__search_context_in_file", "mcp__mcp1__get_trace_structure", "mcp__mcp1__read_multiple_line_ranges"],
                ),
                "Step2": AgentDefinition(
                    description="Structural_Bottleneck_localization",
                    prompt=step2_prompt,
                    tools=["Write", "Read", "Bash", "Glob", "mcp__mcp1__search_context_in_file", "mcp__mcp1__get_trace_structure", "mcp__mcp1__read_multiple_line_ranges"],
                )
            },
        )

        async with ClaudeSDKClient(options=options) as client:
            print(f"Step1: Automated Diagnostic Profiling...")
            await client.query(wrap_prompt("@Step1 Follow the steps in the prompt to automated diagnostic profiling."))
            async for message in client.receive_response():
                formatter.format_message(message)

            print(f"\n\nStep2: Structural Bottleneck localization...")
            await client.query(wrap_prompt("@Step2 Follow the steps in the prompt for structural bottleneck localization."))
            async for message in client.receive_response():
                formatter.format_message(message)
        
        step3_prompt = read_system_prompt("system_prompt/Step3_Inductive_Knowledge_Evolution.md")
        Step3_options = ClaudeAgentOptions(
            system_prompt=step3_prompt,
            mcp_servers={"mcp1": mcp_server},
            allowed_tools=["Task", "Write", "Read", "Bash", "Glob", "mcp__mcp1__search_context_in_file", "mcp__mcp1__get_trace_structure", "mcp__mcp1__read_multiple_line_ranges"],
            permission_mode="default",
            # permission_mode="bypassPermissions", # default
            can_use_tool=can_use_tool_callback,
            cwd=os.getcwd(),
        )

        print(f"\n\nStep3: Inductive Knowledge Evolution...")
            
        async for message in query(
            prompt=wrap_prompt("Follow the steps in the prompt to do the inductive knowledge evolution."),
            options=Step3_options
        ):
            # print("RAW:", message)
            formatter.format_message(message)

        step4_prompt = read_system_prompt("system_prompt/Step4_Scope_Boundary_Validation.md")
        step4_options = ClaudeAgentOptions(
            system_prompt=step4_prompt,
            mcp_servers={"mcp1": mcp_server},
            allowed_tools=["Task", "Write", "Read", "Bash", "Glob", "mcp__mcp1__search_context_in_file", "mcp__mcp1__get_trace_structure", "mcp__mcp1__read_multiple_line_ranges"],
            permission_mode="default",
            # permission_mode="bypassPermissions", # default
            can_use_tool=can_use_tool_callback,
            cwd=os.getcwd(),
        )

        print(f"\n\nStep4: Scope Boundary Validation...")
            
        async for message in query(
            prompt=wrap_prompt("Follow the steps in the prompt to do the scope boundary validation."),
            options=step4_options
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