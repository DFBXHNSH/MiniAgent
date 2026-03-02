"""
Core agent implementation.
"""

from typing import Optional, List, Dict, Any

from src.prompts.system import WORKDIR, SYSTEM, INITIAL_REMINDER, NAG_REMINDER
from src.llm.client import LLMClient
from src.tools import (
    get_all_tools, BASE_TOOLS,
    execute_tools, set_task_handler,
    get_tools_for_agent, AGENT_TYPES,
    get_skill_tool,
    ToolRegistry,
    bash, read_file, write_file, edit_file, todo, run_skill
)
from src.compression import (
    CompressionStrategy, SlidingWindowCompression,
    SemanticSummaryCompression
)
from src.logging.formatter import Logger, ToolCallPrinter
from src.messages.builder import MessageBuilder
from src.agent.subagent import SubAgent


# Cache for all tools to avoid recomputation
_ALL_TOOLS_CACHE = None


def _get_all_tools_cached() -> List[Dict[str, Any]]:
    """Get all tools with caching to avoid repeated evaluation."""
    global _ALL_TOOLS_CACHE
    if _ALL_TOOLS_CACHE is None:
        _ALL_TOOLS_CACHE = get_all_tools()
    return _ALL_TOOLS_CACHE


# Create the default tool registry and register built-in tools
_default_tool_registry = ToolRegistry()

# Register base tools
_default_tool_registry.register()(bash)
_default_tool_registry.register()(read_file)
_default_tool_registry.register()(write_file)
_default_tool_registry.register()(edit_file)
_default_tool_registry.register()(todo)
_default_tool_registry.register()(run_skill)


class BaseAgent:
    """
    A simple LLM agent with tool-calling capabilities.

    Uses litellm to call Qwen models and executes tools.

    Example:
        >>> agent = BaseAgent(model="dashscope/qwen-flash")
        >>> agent.run("List all files in the current directory")
    """

    # ========================================================================
    # Initialization
    # ========================================================================

    def __init__(
        self,
        model: str = "dashscope/qwen-turbo",
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        enable_compression: bool = False,
        compression_interval: int = 20,
        compression_type: str = "auto",
        enable_subagent: bool = False,
    ):
        """
        Initialize the BaseAgent.

        Args:
            model: The model to use (default: dashscope/qwen-turbo)
            system_prompt: Optional custom system prompt
            temperature: Sampling temperature (0.0 for deterministic output)
            max_tokens: Optional max tokens limit
            enable_compression: Enable automatic history compression (default: False)
            compression_interval: Number of turns between automatic compressions
            compression_type: Compression mode - "sliding", "semantic", "auto", or "none"
            enable_subagent: Enable subagent capability via Task tool (default: False)
        """
        # LLM configuration
        self.model = model
        self.system_prompt = system_prompt or SYSTEM
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enable_subagent = enable_subagent
        self.tools = _get_all_tools_cached() if enable_subagent else BASE_TOOLS + [get_skill_tool()]

        # Use tool registry for managing tool functions
        # Create a copy of the default registry for this instance
        self._tool_registry = ToolRegistry()
        for name, func in _default_tool_registry.get_function_map().items():
            self._tool_registry.register(name)(func)

        # Add run_task tool if subagent is enabled
        if enable_subagent:
            from src.tools import run_task
            self._tool_registry.register()(run_task)
            set_task_handler(self._handle_task)

        # Get tool functions list for execute_tools
        self.tool_functions = self._tool_registry.get_all_functions()

        # Initialize components
        self.llm_client = LLMClient(model, temperature, max_tokens)
        self.logger = Logger("Agent")
        self.tool_printer = ToolCallPrinter(self.logger)
        self.message_builder = MessageBuilder()

        # Subagent tracking
        self.subagent_count = 0

        # Skill tracking
        self.skill_count = 0

        # Conversation state
        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.turn_count = 0
        self.last_todo_turn = -1
        self.first_call = True

        # Compression configuration
        self.enable_compression = enable_compression
        self.compression_interval = compression_interval
        self.compression_type = compression_type

        # Compression statistics
        self.compression_stats = {
            "sliding_count": 0,
            "semantic_count": 0,
        }

    # ========================================================================
    # Public API
    # ========================================================================

    def run(self, user_input: str, verbose: bool = False, force_compress: Optional[str] = None) -> str:
        """
        Run a single-turn interaction with the agent.

        Args:
            user_input: The user's message/query
            verbose: If True, print intermediate tool calls and results
            force_compress: Force a specific compression type. Options: "sliding", "semantic", None

        Returns:
            The final assistant response as text
        """
        if verbose:
            self._print_header(user_input)

        self.turn_count += 1

        # Step 1: Handle compression (manual or automatic)
        self._handle_compression(force_compress, verbose)

        # Step 2: Prepare messages for LLM
        messages = self.message_builder.build_copy(
            self.messages, user_input, self.first_call, INITIAL_REMINDER
        )
        self.first_call = False

        if verbose:
            self.logger.log(f"Messages prepared: {len(messages)}", indent=1, emoji="📋")

        # Step 3: Execute LLM and tool loop
        response_message, todo_called = self._execute_tool_loop(messages, verbose)

        # Step 4: Update conversation history
        self.messages = self.messages[:1] + messages[1:]
        if verbose:
            self.logger.log(f"History updated: {len(self.messages)} messages", indent=1)

        # Step 5: Update todo tracking
        self._update_todo_tracking(todo_called, verbose)

        # Step 6: Return assistant's final response
        response_text = self.message_builder.extract_response_text(response_message)
        if verbose:
            self._print_footer(response_text)

        return response_text

    def reset(self):
        """Reset the conversation history, keeping only the system prompt."""
        self.logger.log("Resetting conversation state...", emoji="🔄")
        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.turn_count = 0
        self.last_todo_turn = -1
        self.first_call = True
        self._reset_stats()
        self.logger.log("Conversation reset complete.", indent=1)

    def get_history(self) -> list:
        """Get the current conversation history."""
        return self.messages.copy()

    def get_compression_stats(self) -> Dict[str, int]:
        """Get compression statistics."""
        return self.compression_stats.copy()

    def get_subagent_count(self) -> int:
        """Get the number of subagents spawned by this agent."""
        return self.subagent_count

    def get_skill_count(self) -> int:
        """Get the number of skills used by this agent."""
        return self.skill_count

    def register_tool(self, name: str | None = None):
        """
        Decorator for registering custom tools with this agent.

        Args:
            name: Optional custom name for the tool. If not provided,
                  the function's __name__ is used.

        Returns:
            Decorator function

        Example:
            agent = BaseAgent()

            @agent.register_tool()
            def my_custom_tool(data: str) -> str:
                return f"Processed: {data}"
        """
        return self._tool_registry.register(name)

    def get_tool_names(self) -> List[str]:
        """
        Get a list of all registered tool names.

        Returns:
            List of tool names
        """
        return self._tool_registry.list_names()

    def chat(self, verbose: bool = False):
        """
        Interactive chat mode.

        Args:
            verbose: If True, print intermediate tool calls and results
        """
        self._print_chat_header()

        try:
            while True:
                try:
                    user_input = input("You: ").strip()
                    if not user_input:
                        continue

                    # Handle special commands
                    if user_input.lower() in ("exit", "quit"):
                        self.logger.log("Exiting chat mode...", emoji="👋")
                        break

                    if user_input.lower() == "stats":
                        self._print_stats()
                        continue

                    if user_input.lower() == "reset":
                        self.reset()
                        print("  Conversation reset complete.\n")
                        continue

                    if user_input.lower() == "verbose":
                        verbose = not verbose
                        print(f"  Verbose mode: {'enabled' if verbose else 'disabled'}\n")
                        continue

                    response = self.run(user_input, verbose=verbose)
                    print(f"Agent: {response}\n")

                except Exception as e:
                    print(f"\n  Error: {e}\n")

        except KeyboardInterrupt:
            self.logger.log("\n\nExiting chat mode (interrupted)...", emoji="👋")

    # ========================================================================
    # Subagent Support
    # ========================================================================

    def spawn_subagent(
        self,
        description: str,
        prompt: str,
        agent_type: str = "code",
        verbose: bool = False,
    ) -> str:
        """
        Spawn a subagent to handle a focused subtask.

        Args:
            description: Short task name (3-5 words) for progress display
            prompt: Detailed instructions for the subagent
            agent_type: Type of agent to spawn ("explore", "code", "plan")
            verbose: If True, print subagent progress

        Returns:
            Summary of what the subagent accomplished
        """
        if verbose:
            self._print_subagent_header(description, agent_type)

        # Validate agent_type
        if agent_type not in AGENT_TYPES:
            raise ValueError(
                f"Invalid agent_type '{agent_type}'. "
                f"Valid types: {list(AGENT_TYPES.keys())}"
            )

        # Get configuration for the requested agent type
        agent_config = AGENT_TYPES[agent_type]
        agent_tools = get_tools_for_agent(agent_type, BASE_TOOLS)
        if verbose:
            tool_names = [t['function']['name'] for t in agent_tools]
            self.logger.log(f"Available tools: {tool_names}", indent=1)

        # Build tool function list for subagent
        tool_names = [t["function"]["name"] for t in agent_tools]
        subagent_tool_map = {
            "bash": bash,
            "read_file": read_file,
            "edit_file": edit_file,
            "write_file": write_file,
            "todo": todo,
        }
        subagent_tool_functions = [
            subagent_tool_map[name] for name in tool_names if name in subagent_tool_map
        ]

        # Create subagent with isolated context
        subagent = SubAgent(
            model=self.model,
            tools=agent_tools,
            tool_functions=subagent_tool_functions,
            system_prompt=agent_config["prompt"],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            parent_logger=self.logger,
        )

        # Run subagent
        if verbose:
            print()

        try:
            result = subagent.run(prompt, verbose=verbose)
            self.subagent_count += 1

            if verbose:
                self._print_subagent_footer(result)

            return result
        except Exception as e:
            if verbose:
                self.logger.log(f"Subagent failed: {e}", emoji="❌", indent=1)
                self.logger.separator("▸", 60)
                print()
            return f"Subagent error: {e}"

    def _handle_task(self, description: str, prompt: str, agent_type: str) -> str:
        """Internal handler for Task tool calls from LLM."""
        return self.spawn_subagent(description, prompt, agent_type, verbose=False)

    # ========================================================================
    # LLM and Tool Loop
    # ========================================================================

    def _execute_tool_loop(self, messages: List[Dict[str, Any]], verbose: bool) -> tuple[Any, bool]:
        """Execute the LLM call and tool execution loop."""
        if verbose:
            self.logger.log("Entering tool execution loop...", emoji="🔄")

        todo_called_this_turn = False
        skill_called_this_turn = False
        response_message = None
        loop_count = 0

        while True:
            loop_count += 1
            if verbose:
                self.logger.separator(".", 30)
                self.logger.log(f"Loop iteration #{loop_count}", indent=1)

            # Call LLM
            # import json
            # print(json.dumps(self.tools, indent=2))
            
            response_message = self.llm_client.call(messages, tools=self.tools)
            messages.append(response_message)

            # Print tool calls if verbose
            if verbose and hasattr(response_message, 'tool_calls') and response_message.tool_calls:
                self.tool_printer.print_calls(response_message.tool_calls)
                todo_called_this_turn = self.tool_printer.is_todo_called(response_message)
                skill_called_this_turn = self.tool_printer.is_skill_called(response_message)
            elif verbose:
                self.logger.log("No tool calls in this iteration", indent=1)

            # Execute tools and update history
            has_more_tools, messages = execute_tools(
                messages, response_message, self.tool_functions
            )

            # Print tool results if verbose
            if verbose and has_more_tools:
                self.tool_printer.print_results(messages, response_message.tool_calls)

            # Exit loop if no more tools to call
            if not has_more_tools:
                if verbose:
                    self.logger.log(f"Tool loop completed after {loop_count} iteration(s)", indent=1, emoji="✅")
                break

            # Track skill usage
            if skill_called_this_turn:
                self.skill_count += 1
                if verbose:
                    self.logger.log(f"Skill used this turn. Total skills used: {self.skill_count}", indent=1, emoji="📚")

        return response_message, todo_called_this_turn

    # ========================================================================
    # Compression Management
    # ========================================================================

    def _handle_compression(self, force_compress: Optional[str], verbose: bool) -> None:
        """Handle compression - either manual or automatic."""
        if force_compress:
            self._trigger_manual_compression(force_compress, verbose)
        elif self.enable_compression and self.compression_type != "none":
            if verbose:
                self.logger.log(f"Checking auto compression (type: {self.compression_type})...", emoji="🔍")
            self._trigger_auto_compression(verbose)

    def _trigger_manual_compression(self, compress_type: str, verbose: bool) -> None:
        """Trigger manual compression by type."""
        if verbose:
            self.logger.log(f"Manual compression requested: {compress_type}", emoji="🎛️")

        if compress_type == "sliding":
            strategy = SlidingWindowCompression()
            self.messages = strategy.compress(self.messages, max_turns=10, verbose=verbose)
            self._record_compression("sliding")
        elif compress_type == "semantic":
            strategy = SemanticSummaryCompression(self.llm_client)
            self.messages = strategy.compress(
                self.messages, summary_threshold=5, max_summary_length=200, verbose=verbose
            )
            self._record_compression("semantic")
        else:
            if verbose:
                self.logger.log(f"Warning: unknown compression type '{compress_type}'", emoji="⚠️")

    def _trigger_auto_compression(self, verbose: bool) -> None:
        """Trigger automatic compression based on configuration."""
        msg_count = self.message_builder.get_message_count(self.messages)

        if verbose:
            self.logger.log(f"Current message count: {msg_count}", indent=1)

        if self.compression_type == "sliding":
            if self.turn_count % self.compression_interval == 0:
                strategy = SlidingWindowCompression()
                self.messages = strategy.compress(
                    self.messages, max_turns=self.compression_interval // 2, verbose=verbose
                )
                self._record_compression("sliding")

        elif self.compression_type == "semantic":
            if self.turn_count % self.compression_interval == 0:
                strategy = SemanticSummaryCompression(self.llm_client)
                self.messages = strategy.compress(
                    self.messages, summary_threshold=5, max_summary_length=200, verbose=verbose
                )
                self._record_compression("semantic")

        elif self.compression_type == "auto":
            self._trigger_auto_compress_by_message_count(msg_count, verbose)

    def _trigger_auto_compress_by_message_count(self, msg_count: int, verbose: bool) -> None:
        """Auto mode: choose compression type based on message count."""
        # High message count: use semantic summary
        if msg_count > 40 and self.turn_count % self.compression_interval == 0:
            strategy = SemanticSummaryCompression(self.llm_client)
            self.messages = strategy.compress(
                self.messages, summary_threshold=10, max_summary_length=300, verbose=verbose
            )
            self._record_compression("semantic")

        # Medium message count: use sliding window
        elif msg_count > 20 and self.turn_count % (self.compression_interval // 2) == 0:
            strategy = SlidingWindowCompression()
            self.messages = strategy.compress(self.messages, max_turns=15, verbose=verbose)
            self._record_compression("sliding")

    def _record_compression(self, compress_type: str) -> None:
        """Record a compression event in statistics."""
        if compress_type == "sliding":
            self.compression_stats["sliding_count"] += 1
        elif compress_type == "semantic":
            self.compression_stats["semantic_count"] += 1

    def _reset_compression_stats(self) -> None:
        """Reset compression statistics."""
        self.compression_stats = {
            "sliding_count": 0,
            "semantic_count": 0,
        }

    def _reset_stats(self) -> None:
        """Reset all statistics."""
        self._reset_compression_stats()
        self.subagent_count = 0
        self.skill_count = 0

    # ========================================================================
    # TODO Tracking
    # ========================================================================

    def _update_todo_tracking(self, todo_called_this_turn: bool, verbose: bool) -> None:
        """Update todo tracking and add NAG reminder if needed."""
        if todo_called_this_turn:
            self.last_todo_turn = self.turn_count
            if verbose:
                self.logger.log("Todo tool called - tracking updated", emoji="📝")

        if self._should_add_nag_reminder():
            self._add_nag_reminder(verbose)

    def _should_add_nag_reminder(self) -> bool:
        """Check if NAG reminder should be added."""
        turns_since_todo = self.turn_count - self.last_todo_turn
        return turns_since_todo >= 10

    def _add_nag_reminder(self, verbose: bool) -> None:
        """Add the NAG reminder message to conversation history."""
        if verbose:
            self.logger.log(f"Adding NAG reminder (turns since todo: {self.turn_count - self.last_todo_turn})", emoji="⚠️")
        self.messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": NAG_REMINDER}, #type: ignore
                {"type": "text", "text": "placeholder"}
            ]
        })
        self.last_todo_turn = self.turn_count

    # ========================================================================
    # Display Helpers
    # ========================================================================

    def _print_header(self, user_input: str) -> None:
        """Print header for verbose mode."""
        self.logger.separator("=", 60)
        self.logger.log(f"NEW TURN #{self.turn_count + 1}", emoji="🔄")
        self.logger.log(f"Model: {self.model}", indent=1)
        self.logger.log(f"Input: {user_input[:100]}{'...' if len(user_input) > 100 else ''}", indent=1)
        self.logger.log(f"Messages in history: {len(self.messages)}", indent=1)
        self.logger.separator("-", 40)

    def _print_footer(self, response_text: str) -> None:
        """Print footer for verbose mode."""
        self.logger.log(f"Response: {response_text[:150]}{'...' if len(response_text) > 150 else ''}", indent=1, emoji="💬")
        self.logger.separator("=", 60)
        print()

    def _print_chat_header(self) -> None:
        """Print header for chat mode."""
        self.logger.separator("=", 60)
        print(f"  🤖 BaseAgent Chat Mode")
        print(f"  Model: {self.model}")
        print(f"  Subagent enabled: {self.enable_subagent}")
        print(f"  Compression: {self.compression_type if self.enable_compression else 'disabled'}")
        self.logger.separator("=", 60)
        print()
        print("Commands:")
        print("  - Type your message to chat with the agent")
        print("  - Type 'exit' or 'quit' to leave")
        print("  - Type 'stats' to show compression statistics")
        print("  - Type 'reset' to reset conversation history")
        print("  - Type 'verbose' to toggle verbose mode")
        print()

    def _print_stats(self) -> None:
        """Print statistics."""
        stats = self.get_compression_stats()
        self.logger.separator("-", 40)
        print("  Compression Statistics:")
        print(f"    Sliding window: {stats['sliding_count']}")
        print(f"    Semantic summary: {stats['semantic_count']}")
        print("  Agent Statistics:")
        print(f"    Skills used: {self.skill_count}")
        print(f"    Subagents spawned: {self.subagent_count}")
        print(f"    Total turns: {self.turn_count}")
        self.logger.separator("-", 40)
        print()

    def _print_subagent_header(self, description: str, agent_type: str) -> None:
        """Print header for subagent spawning."""
        self.logger.separator("▸", 60)
        self.logger.log(f"SPAWNING SUBAGENT ({agent_type})", emoji="🚀")
        self.logger.log(f"Description: {description}", indent=1)

    def _print_subagent_footer(self, result: str) -> None:
        """Print footer for subagent completion."""
        self.logger.log(f"SUBAGENT COMPLETED", emoji="✅")
        self.logger.log(f"Result: {result[:200]}{'...' if len(result) > 200 else ''}", indent=1)
        self.logger.separator("▸", 60)
        print()
