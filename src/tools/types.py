"""
Agent type definitions and tool filtering.

This module defines the different agent types and their tool permissions.
"""

from typing import List, Dict, Any


# Agent Type Registry
AGENT_TYPES = {
    # Explore: Read-only agent for searching and analyzing
    # Cannot modify files - safe for broad exploration
    "explore": {
        "description": "Read-only agent for exploring code, finding files, searching",
        "tools": ["bash", "read_file"],
        "prompt": "You are an exploration agent. Search and analyze, but never modify files. Return a concise summary.",
    },

    # Code: Full-powered agent for implementation
    # Has all tools - use for actual coding work
    "code": {
        "description": "Full agent for implementing features and fixing bugs",
        "tools": "*",
        "prompt": "You are a coding agent. Implement the requested changes efficiently.",
    },

    # Plan: Analysis agent for design work
    # Read-only, focused on producing plans and strategies
    "plan": {
        "description": "Planning agent for designing implementation strategies",
        "tools": ["bash", "read_file"],
        "prompt": "You are a planning agent. Analyze the codebase and output a numbered implementation plan. Do NOT make changes.",
    },
}


def get_agent_descriptions() -> str:
    """
    Generate agent type descriptions for display.

    Returns:
        A formatted string of agent type descriptions
    """
    return "\n".join(
        f"- {name}: {cfg['description']}"
        for name, cfg in AGENT_TYPES.items()
    )


def get_tools_for_agent(
    agent_type: str,
    all_tools: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Filter tools based on agent type.

    Each agent type has a whitelist of allowed tools.
    '*' means all tools.

    Args:
        agent_type: The type of agent
        all_tools: All available tool definitions

    Returns:
        Filtered list of tools for the agent type
    """
    allowed = AGENT_TYPES.get(agent_type, {}).get("tools", "*")

    if allowed == "*":
        return all_tools

    return [t for t in all_tools if t["function"]["name"] in allowed]
