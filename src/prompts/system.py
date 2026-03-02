"""
System prompts for the agent.
"""

import os
from pathlib import Path


def get_workdir() -> Path:
    """
    Get the working directory for the agent.

    The workdir can be configured via:
    1. Environment variable MINI_AGENT_WORKDIR
    2. Current working directory (default)

    Returns:
        The working directory as a Path object
    """
    env_workdir = os.getenv("MINI_AGENT_WORKDIR")
    if env_workdir:
        return Path(env_workdir).expanduser().resolve()
    return Path.cwd()


def get_system_prompt(workdir: Path | None = None) -> str:
    """
    Get the system prompt for the agent.

    Args:
        workdir: Optional working directory. If not provided, uses get_workdir().

    Returns:
        The system prompt string
    """
    if workdir is None:
        workdir = get_workdir()

    return f"""You are a coding agent at {workdir}.

Loop: plan -> act with tools -> report.

You can spawn subagents for complex subtasks.
Use TodoWrite to track multi-step work.
Use the skill tool IMMEDIATELY when a task matches a skill description.
Prefer tools over prose. Act, don't just explain.
After finishing, summarize what changed."""


# Default workdir (can be overridden via get_workdir())
WORKDIR = get_workdir()

# System prompt (legacy export for backward compatibility)
SYSTEM = get_system_prompt()

INITIAL_REMINDER = "<reminder>Use TodoWrite for multi-step tasks.</reminder>"

NAG_REMINDER = "<reminder>10+ turns without todo update. Please update todos.</reminder>"
