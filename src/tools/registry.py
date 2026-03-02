"""
Tool registration system for extensible tool management.

This module provides a decorator-based pattern for registering tools,
making it easier to add new tools without modifying core code.
"""

from typing import Callable, Dict, List


class ToolRegistry:
    """
    Registry for managing tool functions.

    Tools can be registered using the @register_tool decorator.
    The registry maintains a mapping of tool names to their implementations.
    """

    def __init__(self):
        """Initialize an empty tool registry."""
        self._tools: Dict[str, Callable] = {}

    def register(self, name: str | None = None) -> Callable:
        """
        Decorator for registering a tool function.

        Args:
            name: Optional custom name for the tool. If not provided,
                  the function's __name__ is used.

        Returns:
            Decorator function

        Example:
            registry = ToolRegistry()

            @registry.register()
            def my_tool(arg: str) -> str:
                return f"Processed: {arg}"
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name if name is not None else func.__name__
            self._tools[tool_name] = func
            return func
        return decorator

    def get(self, name: str) -> Callable | None:
        """
        Get a tool function by name.

        Args:
            name: The name of the tool

        Returns:
            The tool function, or None if not found
        """
        return self._tools.get(name)

    def list_names(self) -> List[str]:
        """
        Get a list of all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def get_all_functions(self) -> List[Callable]:
        """
        Get all registered tool functions.

        Returns:
            List of all tool functions
        """
        return list(self._tools.values())

    def get_function_map(self) -> Dict[str, Callable]:
        """
        Get the complete tool name to function mapping.

        Returns:
            Dictionary mapping tool names to their functions
        """
        return self._tools.copy()

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()

    def __len__(self) -> int:
        """Get the number of registered tools."""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools
