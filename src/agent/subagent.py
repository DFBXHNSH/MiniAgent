"""
Subagent implementation.

Subagents run in isolated context and don't have access to parent's history.
They also don't have the Task tool to prevent infinite recursion.
"""

from typing import Any, List, Dict, Optional

from src.llm.client import LLMClient
from src.tools import execute_tools
from src.logging.formatter import Logger, ToolCallPrinter
from src.messages.builder import MessageBuilder


class SubAgent:
    """
    A lightweight agent for subagent execution.

    Subagents run in isolated context and don't have access to parent's history.
    They also don't have the Task tool to prevent infinite recursion.
    """

    def __init__(
        self,
        model: str,
        tools: List[Dict[str, Any]],
        tool_functions: List[Any],
        system_prompt: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        parent_logger: Optional[Logger] = None,
    ):
        """
        Initialize the SubAgent.

        Args:
            model: The model to use (inherited from parent)
            tools: List of tool definitions for this agent type
            tool_functions: List of callable tool functions
            system_prompt: The agent type specific system prompt
            temperature: Sampling temperature (inherited from parent)
            max_tokens: Max tokens limit (inherited from parent)
            parent_logger: Optional parent logger for shared logging
        """
        self.model = model
        self.tools = tools
        self.tool_functions = tool_functions
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Use parent logger or create new one
        self.logger = parent_logger or Logger("SubAgent")
        self.tool_printer = ToolCallPrinter(self.logger)
        self.llm_client = LLMClient(model, temperature, max_tokens)

    def run(self, user_input: str, verbose: bool = False) -> str:
        """
        Run the subagent with the given prompt.

        Args:
            user_input: The prompt/instructions for the subagent
            verbose: If True, print intermediate tool calls and results

        Returns:
            The final response from the subagent
        """
        if verbose:
            self.logger.log("Starting subagent execution...", emoji="▶️")
            self.logger.log(f"Input: {user_input[:100]}{'...' if len(user_input) > 100 else ''}", indent=1)

        # Start with fresh conversation history (isolated from parent)
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.append({"role": "user", "content": user_input})

        loop_count = 0

        # Execute LLM and tool loop
        while True:
            loop_count += 1
            if verbose:
                self.logger.separator(".", 25)
                self.logger.log(f"Loop iteration #{loop_count}", indent=1)

            # Call LLM
            if verbose:
                self.logger.log("Calling LLM...", indent=1, emoji="🤖")

            response_message = self.llm_client.call(messages, tools=self.tools)
            messages.append(response_message)

            # Check for tool calls
            tool_calls = getattr(response_message, "tool_calls", None)
            if not tool_calls:
                # No more tools - return the response
                if verbose:
                    self.logger.log("No tool calls - returning response", indent=1)
                    result = MessageBuilder.extract_response_text(response_message)
                    self.logger.log(f"Result: {result[:150]}{'...' if len(result) > 150 else ''}", indent=1, emoji="✅")
                return MessageBuilder.extract_response_text(response_message)

            # Print tool calls if verbose
            if verbose:
                self.logger.log(f"LLM returned {len(tool_calls)} tool call(s)", indent=1, emoji="🔧")
                self.tool_printer.print_calls(tool_calls)

            # Execute tools
            has_more_tools, messages = execute_tools(
                messages, response_message, self.tool_functions
            )

            # Print tool results if verbose
            if verbose and has_more_tools:
                self.tool_printer.print_results(messages, tool_calls)

            # Loop continues until no more tool calls
