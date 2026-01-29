"""
Beautiful formatter for Claude Agent SDK message output
"""

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

        # Determine message type
        if msg_str.startswith('UserMessage'):
            self._format_user_message(message, msg_str)
        elif msg_str.startswith('AssistantMessage'):
            self._format_assistant_message(message, msg_str)
        elif msg_str.startswith('ResultMessage'):
            self._format_result_message(message, msg_str)
        else:
            # Fallback for unknown message types
            print(f"{Colors.DIM}[Message {self.message_count}]{Colors.RESET}")
            print(f"{Colors.WHITE}{msg_str}{Colors.RESET}\n")

    def _format_user_message(self, message, msg_str):
        """Format user messages (typically tool results)"""
        print(f"\n{Colors.DIM}{'─' * 80}{Colors.RESET}")
        print(f"{Colors.DIM}[Message {self.message_count}]{Colors.RESET}")

        if 'ToolResultBlock' in msg_str:
            # Extract content from tool result
            content = self._extract_content(msg_str)
            is_error = 'is_error=True' in msg_str

            if is_error:
                print(f"{Colors.BOLD}{Colors.RED}❌ Tool Result (Error){Colors.RESET}")
                print(f"{Colors.RED}  {content}{Colors.RESET}")
            else:
                print(f"{Colors.BOLD}{Colors.GREEN}✅ Tool Result{Colors.RESET}")
                print(f"{Colors.GREEN}  {content}{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}📥 User Message{Colors.RESET}")
            print(f"{Colors.WHITE}  {msg_str}{Colors.RESET}")

    def _format_assistant_message(self, message, msg_str):
        """Format assistant messages (text or tool use)"""
        print(f"\n{Colors.DIM}{'─' * 80}{Colors.RESET}")
        print(f"{Colors.DIM}[Message {self.message_count}]{Colors.RESET}")

        if 'TextBlock' in msg_str:
            # Extract and format text
            text = self._extract_text(msg_str)
            print(f"{Colors.BOLD}{Colors.BLUE}💬 Assistant:{Colors.RESET}")

            # Format the text with proper indentation
            for line in text.split('\\n'):
                if line.strip():
                    # Detect headers and special formatting
                    if line.startswith('##'):
                        print(f"{Colors.BOLD}{Colors.CYAN}  {line}{Colors.RESET}")
                    elif line.strip().startswith('✅') or line.strip().startswith('-'):
                        print(f"{Colors.WHITE}  {line}{Colors.RESET}")
                    else:
                        print(f"{Colors.WHITE}  {line}{Colors.RESET}")
                else:
                    print()

        elif 'ToolUseBlock' in msg_str:
            # Extract tool information
            tool_name = self._extract_tool_name(msg_str)
            tool_input = self._extract_tool_input(msg_str)

            print(f"{Colors.BOLD}{Colors.YELLOW}🔧 Tool Call: {Colors.MAGENTA}{tool_name}{Colors.RESET}")

            if tool_input:
                for key, value in tool_input.items():
                    if key == 'command':
                        print(f"{Colors.BOLD}  Command:{Colors.RESET} {Colors.CYAN}{value}{Colors.RESET}")
                    elif key == 'description':
                        print(f"{Colors.BOLD}  Description:{Colors.RESET} {Colors.WHITE}{value}{Colors.RESET}")
                    else:
                        print(f"{Colors.BOLD}  {key}:{Colors.RESET} {Colors.WHITE}{value}{Colors.RESET}")

    def _format_result_message(self, message, msg_str):
        """Format final result message with metadata"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}📊 Final Result Summary{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")

        # Extract metadata
        metadata = self._extract_metadata(msg_str)

        if metadata.get('subtype'):
            status_icon = "✅" if metadata['subtype'] == 'success' else "❌"
            print(f"{Colors.BOLD}Status:{Colors.RESET} {status_icon} {metadata['subtype'].upper()}")

        if metadata.get('duration_ms'):
            duration_s = metadata['duration_ms'] / 1000
            print(f"{Colors.BOLD}Duration:{Colors.RESET} {duration_s:.2f}s")

        if metadata.get('num_turns'):
            print(f"{Colors.BOLD}Turns:{Colors.RESET} {metadata['num_turns']}")

        if metadata.get('total_cost_usd'):
            print(f"{Colors.BOLD}Cost:{Colors.RESET} ${metadata['total_cost_usd']:.4f}")

        # Token usage
        if 'usage=' in msg_str:
            print(f"\n{Colors.BOLD}{Colors.YELLOW}Token Usage:{Colors.RESET}")
            usage = self._extract_usage(msg_str)
            if usage:
                for key, value in usage.items():
                    if isinstance(value, int):
                        print(f"  {key}: {value:,}")

        # Extract and format result text
        result_text = self._extract_result_text(msg_str)
        if result_text:
            print(f"\n{Colors.BOLD}{Colors.GREEN}Result:{Colors.RESET}")
            for line in result_text.split('\\n'):
                if line.strip():
                    if line.startswith('##'):
                        print(f"{Colors.BOLD}{Colors.CYAN}  {line}{Colors.RESET}")
                    else:
                        print(f"{Colors.WHITE}  {line}{Colors.RESET}")
                else:
                    print()

    def _extract_content(self, msg_str):
        """Extract content from tool result"""
        import re
        match = re.search(r"content='([^']*)'", msg_str)
        return match.group(1) if match else ""

    def _extract_text(self, msg_str):
        """Extract text from TextBlock"""
        import re
        match = re.search(r"text='([^']+(?:\\'[^']*)*)'", msg_str)
        if match:
            return match.group(1).replace("\\'", "'")
        return ""

    def _extract_tool_name(self, msg_str):
        """Extract tool name from ToolUseBlock"""
        import re
        match = re.search(r"name='([^']+)'", msg_str)
        return match.group(1) if match else "Unknown"

    def _extract_tool_input(self, msg_str):
        """Extract tool input from ToolUseBlock"""
        import re
        match = re.search(r"input=({[^}]+})", msg_str)
        if match:
            try:
                return eval(match.group(1))
            except:
                return {}
        return {}

    def _extract_metadata(self, msg_str):
        """Extract metadata from ResultMessage"""
        import re
        metadata = {}

        fields = ['subtype', 'duration_ms', 'duration_api_ms', 'num_turns', 'total_cost_usd']
        for field in fields:
            match = re.search(rf"{field}='?([^',\s]+)'?,", msg_str)
            if match:
                value = match.group(1).replace("'", "")
                try:
                    if 'ms' in field or 'usd' in field or 'turns' in field:
                        metadata[field] = float(value) if '.' in value else int(value)
                    else:
                        metadata[field] = value
                except:
                    metadata[field] = value

        return metadata

    def _extract_usage(self, msg_str):
        """Extract usage information from ResultMessage"""
        import re
        match = re.search(r"usage=({.+?}(?:, '|\)$))", msg_str)
        if match:
            try:
                usage_str = match.group(1).rstrip(", ')").rstrip(')')
                usage_dict = eval(usage_str)
                # Flatten nested dicts for simpler display
                flat_usage = {}
                for key, value in usage_dict.items():
                    if isinstance(value, dict):
                        continue  # Skip nested dicts for now
                    elif isinstance(value, int):
                        flat_usage[key] = value
                return flat_usage
            except:
                return {}
        return {}

    def _extract_result_text(self, msg_str):
        """Extract result text from ResultMessage"""
        import re
        match = re.search(r"result='([^']+(?:\\'[^']*)*)'", msg_str)
        if match:
            return match.group(1).replace("\\'", "'")
        return ""