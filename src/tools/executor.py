"""
Tool execution engine.

This module handles the execution of tool calls returned by the LLM.
"""

import json
from typing import List, Dict, Any, Callable


def execute_tools(
    history: List[Dict[str, Any]],
    response_message: Any,
    tool_funcs: List[Callable]
) -> tuple[bool, List[Dict[str, Any]]]:
    """
    Execute all tools returned by LLM and maintain history.

    Args:
        history: The conversation history (list of message dicts)
        response_message: The response message from LLM containing tool_calls
        tool_funcs: A list of callable functions that can be called by name

    Returns:
        A tuple of (has_more_tools, updated_history):
        - has_more_tools: True if there were tools executed, False if no tools
        - updated_history: The history with response and tool results appended

    Example:
        >>> response = completion(model="...", messages=history, tools=tools)
        >>> response_msg = response.choices[0].message
        >>> has_more, history = execute_tools(history, response_msg, tool_functions)
    """
    # Build a name-to-function mapping from tool_funcs
    func_map = {f.__name__: f for f in tool_funcs}

    # Get tool calls from response
    tool_calls = getattr(response_message, "tool_calls", None)

    if not tool_calls:
        # No tools to execute
        return False, history

    # Execute all tools and append results to history
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        # Match and execute the tool using **args
        func = func_map.get(function_name)
        if func is None:
            function_response = f"Error: Tool '{function_name}' not found in {list(func_map.keys())}"
        else:
            try:
                function_response = func(**function_args)
            except TypeError as e:
                function_response = f"Error: Invalid arguments for {function_name}: {e}"
            except Exception as e:
                function_response = f"Error: {e}"

        # Append tool result to history
        history.append({
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": function_name,
            "content": function_response,
        })

    return True, history
