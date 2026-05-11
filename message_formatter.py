"""
Beautiful formatter for Claude Agent SDK message output
"""

import json
from datetime import datetime


# ANSI Color Codes for beautiful terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Regular colors
    BLACK = '\033[30m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

    # Background colors
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'
    BG_BLUE = '\033[104m'


class MessageFormatter:
    """Beautiful formatter for Claude Agent SDK messages"""

    def __init__(self):
        self.message_count = 0
        self.start_time = datetime.now()

    def print_header(self):
        """Print a beautiful header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}🤖  Claude Agent SDK - Conversation Output{Colors.RESET}")
        print(f"{Colors.DIM}Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")

    def print_footer(self):
        """Print a beautiful footer with summary"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}✅ Conversation Completed{Colors.RESET}")
        print(f"{Colors.DIM}Duration: {duration:.2f}s | Messages: {self.message_count}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")

    def format_message(self, message):
        """Format and print a message beautifully"""
        self.message_count += 1
        msg_str = str(message)
        msg_type = type(message).__name__

        # Determine message type
        if msg_type == 'UserMessage':
            self._format_user_message(message, msg_str)
        elif msg_type == 'AssistantMessage':
            self._format_assistant_message(message, msg_str)
        elif msg_type == 'ResultMessage':
            self._format_result_message(message, msg_str)
        elif msg_type == 'SystemMessage':
            self._format_system_message(message, msg_str)
        else:
            # Fallback for unknown message types
            print(f"{Colors.DIM}[Message {self.message_count}]{Colors.RESET}")
            print(f"{Colors.WHITE}{msg_str}{Colors.RESET}\n")

    def _format_user_message(self, message, msg_str):
        """Format user messages (typically tool results)"""
        print(f"\n{Colors.DIM}{'─' * 80}{Colors.RESET}")
        print(f"{Colors.DIM}[Message {self.message_count}]{Colors.RESET}")

        content = getattr(message, 'content', None)
        if isinstance(content, list):
            if not content:
                print(f"{Colors.YELLOW}📥 User Message{Colors.RESET}")
                print(f"{Colors.WHITE}  <empty>{Colors.RESET}")
            for block in content:
                self._format_content_block(block, user_block=True)
        elif content is not None:
            print(f"{Colors.YELLOW}📥 User Message{Colors.RESET}")
            self._print_text(self._format_value(content), Colors.WHITE)
        else:
            print(f"{Colors.YELLOW}📥 User Message{Colors.RESET}")
            self._print_text(msg_str, Colors.WHITE)

    def _format_assistant_message(self, message, msg_str):
        """Format assistant messages (text or tool use)"""
        print(f"\n{Colors.DIM}{'─' * 80}{Colors.RESET}")
        print(f"{Colors.DIM}[Message {self.message_count}]{Colors.RESET}")

        content = getattr(message, 'content', None)
        if isinstance(content, list):
            if not content:
                print(f"{Colors.BOLD}{Colors.BLUE}💬 Assistant:{Colors.RESET}")
                print(f"{Colors.WHITE}  <empty>{Colors.RESET}")
            for block in content:
                self._format_content_block(block)
        elif content is not None:
            print(f"{Colors.BOLD}{Colors.BLUE}💬 Assistant:{Colors.RESET}")
            self._print_text(self._format_value(content), Colors.WHITE)
        else:
            self._print_text(msg_str, Colors.WHITE)

    def _format_result_message(self, message, msg_str):
        """Format final result message with metadata"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}📊 Final Result Summary{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")

        subtype = getattr(message, 'subtype', None)
        if subtype:
            status_icon = "✅" if subtype == 'success' else "❌"
            print(f"{Colors.BOLD}Status:{Colors.RESET} {status_icon} {subtype.upper()}")

        duration_ms = getattr(message, 'duration_ms', None)
        if duration_ms is not None:
            duration_s = duration_ms / 1000
            print(f"{Colors.BOLD}Duration:{Colors.RESET} {duration_s:.2f}s")

        num_turns = getattr(message, 'num_turns', None)
        if num_turns is not None:
            print(f"{Colors.BOLD}Turns:{Colors.RESET} {num_turns}")

        total_cost_usd = getattr(message, 'total_cost_usd', None)
        if total_cost_usd is not None:
            print(f"{Colors.BOLD}Cost:{Colors.RESET} ${total_cost_usd:.4f}")

        # Token usage
        usage = getattr(message, 'usage', None)
        if usage:
            print(f"\n{Colors.BOLD}{Colors.YELLOW}Token Usage:{Colors.RESET}")
            for key, value in usage.items():
                if isinstance(value, int):
                    print(f"  {key}: {value:,}")
                elif not isinstance(value, dict):
                    print(f"  {key}: {value}")

        # Extract and format result text
        result_text = getattr(message, 'result', None)
        if result_text:
            print(f"\n{Colors.BOLD}{Colors.GREEN}Result:{Colors.RESET}")
            self._print_text(result_text, Colors.WHITE)

        structured_output = getattr(message, 'structured_output', None)
        if structured_output is not None:
            print(f"\n{Colors.BOLD}{Colors.GREEN}Structured Output:{Colors.RESET}")
            self._print_text(self._format_value(structured_output), Colors.WHITE)

    def _format_system_message(self, message, msg_str):
        """Format system messages."""
        print(f"\n{Colors.DIM}{'─' * 80}{Colors.RESET}")
        print(f"{Colors.DIM}[Message {self.message_count}]{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}⚙️  System Message:{Colors.RESET}")
        data = getattr(message, 'data', None)
        self._print_text(self._format_value(data if data is not None else msg_str), Colors.WHITE)

    def _format_content_block(self, block, user_block=False):
        """Format one SDK content block without parsing repr strings."""
        block_type = type(block).__name__
        if block_type == 'TextBlock':
            label = '📥 User Message' if user_block else '💬 Assistant:'
            color = Colors.YELLOW if user_block else Colors.BLUE
            print(f"{Colors.BOLD}{color}{label}{Colors.RESET}")
            self._print_text(getattr(block, 'text', ''), Colors.WHITE)
        elif block_type == 'ThinkingBlock':
            print(f"{Colors.BOLD}{Colors.MAGENTA}🧠 Thinking:{Colors.RESET}")
            self._print_text(getattr(block, 'thinking', ''), Colors.DIM)
        elif block_type == 'ToolUseBlock':
            self._format_tool_call_block(block)
        elif block_type == 'ToolResultBlock':
            self._format_tool_result_block(block)
        else:
            print(f"{Colors.BOLD}{Colors.WHITE}{block_type}:{Colors.RESET}")
            self._print_text(self._format_value(block), Colors.WHITE)

    def _format_tool_call_block(self, block):
        """Format a ToolUseBlock."""
        tool_name = getattr(block, 'name', 'Unknown')
        tool_input = getattr(block, 'input', None)
        print(f"{Colors.BOLD}{Colors.YELLOW}🔧 Tool Call: {Colors.MAGENTA}{tool_name}{Colors.RESET}")
        if isinstance(tool_input, dict):
            for key, value in tool_input.items():
                label = key.replace('_', ' ').title()
                value_color = Colors.CYAN if key == 'command' else Colors.WHITE
                self._print_labeled_value(label, value, value_color)
        elif tool_input is not None:
            self._print_labeled_value('Input', tool_input, Colors.WHITE)

    def _format_tool_result_block(self, block):
        """Format a ToolResultBlock."""
        content = getattr(block, 'content', None)
        is_error = bool(getattr(block, 'is_error', False))
        if is_error:
            print(f"{Colors.BOLD}{Colors.RED}❌ Tool Result (Error){Colors.RESET}")
            self._print_text(self._format_value(content), Colors.RED)
        else:
            print(f"{Colors.BOLD}{Colors.GREEN}✅ Tool Result{Colors.RESET}")
            self._print_text(self._format_value(content), Colors.GREEN)

    def _format_value(self, value):
        """Convert arbitrary SDK values to printable text without executing them."""
        if value is None:
            return 'None'
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value, ensure_ascii=False, indent=2)
        except TypeError:
            return str(value)

    def _print_labeled_value(self, label, value, color):
        """Print a key/value pair, preserving multiline values."""
        text = self._format_value(value)
        if '\n' in text:
            print(f"{Colors.BOLD}  {label}:{Colors.RESET}")
            self._print_text(text, color)
        else:
            print(f"{Colors.BOLD}  {label}:{Colors.RESET} {color}{text}{Colors.RESET}")

    def _print_text(self, text, color):
        """Print text with indentation while preserving every line."""
        text = '' if text is None else str(text)
        lines = text.splitlines()
        if not lines:
            print(f"{color}  {text}{Colors.RESET}")
            return
        for line in lines:
            if line.startswith('##'):
                print(f"{Colors.BOLD}{Colors.CYAN}  {line}{Colors.RESET}")
            else:
                print(f"{color}  {line}{Colors.RESET}")
