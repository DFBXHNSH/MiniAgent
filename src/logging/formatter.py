"""
Internal logging and formatting utilities for agent output.

This module provides logging capabilities with timestamps and tool call
pretty-printing functionality. It is designed for internal use within the
agent framework.
"""

import sys
from datetime import datetime
from typing import Any, List, Dict, Optional


def _safe_print(message: str) -> None:
    """Print a message safely, handling encoding errors on Windows."""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback: replace unencodable characters
        print(message.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))


class Logger:
    """
    Internal logger with timestamp and indentation support.

    Used for agent-internal logging with structured output.
    """

    def __init__(self, name: str = "Agent"):
        self.name = name

    def log(self, message: str, indent: int = 0, emoji: str = "") -> None:
        """
        Log a message with timestamp and optional indentation/emoji.

        Args:
            message: The message to log
            indent: Number of indentation levels (each level = 2 spaces)
            emoji: Optional emoji to prefix the message
        """
        prefix = "  " * indent
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        emoji_prefix = f"{emoji} " if emoji else ""
        _safe_print(f"[{timestamp}] [{self.name}] {prefix}{emoji_prefix}{message}")

    def separator(self, char: str = "-", length: int = 50) -> None:
        """Print a separator line for visual clarity."""
        _safe_print(f"  [{self.name}] {char * length}")


class ToolCallPrinter:
    """
    Pretty printer for tool calls and results.

    Formats tool invocations and their results in a readable manner.
    """

    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or Logger()

    def print_calls(self, tool_calls: List[Any]) -> None:
        """
        Print tool calls in a formatted way.

        Args:
            tool_calls: List of tool call objects from LLM response
        """
        if not tool_calls:
            return

        _safe_print("")
        self.logger.log("Tool Calls:", emoji="🔧", indent=1)
        for i, tc in enumerate(tool_calls, 1):
            tool_name = tc.function.name
            args = tc.function.arguments
            emoji = "📝" if tool_name == "todo" else "⚙️"
            preview = args[:80] + "..." if len(args) > 80 else args
            self.logger.log(f"{i}. {tool_name}({preview})", indent=2, emoji=emoji)

    def print_results(self, messages: List[Dict[str, Any]], tool_calls: List[Any]) -> None:
        """
        Print tool results in a formatted way.

        Args:
            messages: Current message history (including tool results)
            tool_calls: Tool calls that were made
        """
        if not tool_calls:
            return

        _safe_print("")
        self.logger.log("Tool Results:", emoji="📊", indent=1)
        tool_call_count = len(tool_calls)
        for i, msg in enumerate(messages[-tool_call_count:], 1):
            if msg.get("role") == "tool":
                tool_name = msg.get('name', 'unknown')
                content = msg.get('content', '')
                display_content = content[:150] + '...' if len(content) > 150 else content
                self.logger.log(f"{i}. {tool_name}: {display_content}", indent=2, emoji="✅")
        _safe_print("")

    @staticmethod
    def is_todo_called(response_message: Any) -> bool:
        """
        Check if the todo tool was called in the response.

        Args:
            response_message: The response message from LLM

        Returns:
            True if todo was called, False otherwise
        """
        if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
            for tc in response_message.tool_calls:
                if tc.function.name == "todo":
                    return True
        return False

    @staticmethod
    def is_skill_called(response_message: Any) -> bool:
        """
        Check if the skill tool was called in the response.

        Args:
            response_message: The response message from LLM

        Returns:
            True if skill was called, False otherwise
        """
        # import json
        # print(json.dumps(response_message.to_dict(), indent=2))
        if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
            for tc in response_message.tool_calls:
                #print(tc.function.name)
                if tc.function.name == "run_skill":
                    return True
        return False
