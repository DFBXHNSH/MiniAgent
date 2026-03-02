"""
Tool definitions in OpenAI Function Calling format.

This module contains the schema definitions for tools that the agent can call.
"""

from src.tools.types import get_agent_descriptions

# Lazy import to avoid circular dependency with src/__init__.py
# SKILLS is only used at module load time for tool descriptions
def _get_skills():
    from src.skills import SKILLS
    return SKILLS


def _get_skill_descriptions():
    """Get skill descriptions lazily to avoid circular import."""
    return _get_skills().get_descriptions()


# Base tools available to all agents
BASE_TOOLS = [
    # Tool 1: Bash - The gateway to everything
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command. Use for: ls, find, grep, git, npm, python, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute",
                    }
                },
                "required": ["command"],
            },
        },
    },
    # Tool 2: Read File
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read file contents. Use limit for large files to read only first N lines. Returns UTF-8 text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to read (relative to workspace)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Optional: Number of lines to read (for large files, default: all)",
                    },
                },
                "required": ["path"],
            },
        },
    },
    # Tool 3: Write File
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates parent directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to write (relative to workspace)",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    # Tool 4: Edit File
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace exact text in a file. Only replaces first occurrence for safety. Use for surgical edits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to edit (relative to workspace)",
                    },
                    "old_text": {
                        "type": "string",
                        "description": "The exact text to replace (must match verbatim)",
                    },
                    "new_text": {
                        "type": "string",
                        "description": "The new text to replace with",
                    },
                },
                "required": ["path", "old_text", "new_text"],
            },
        },
    },
    # Tool 5: TodoWrite
    {
        "type": "function",
        "function": {
            "name": "todo",
            "description": "Update the todo list. Send a complete new list (not a diff) with items having content, status (pending|in_progress|completed), and activeForm (present tense form shown during in_progress).",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "List of todo items",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "description": "Task description"
                                },
                                "status": {
                                    "type": "string",
                                    "enum": ["pending", "in_progress", "completed"],
                                    "description": "Task status"
                                },
                                "activeForm": {
                                    "type": "string",
                                    "description": "Present tense form shown during in_progress (e.g., 'Adding unit tests...')"
                                }
                            },
                            "required": ["content", "status", "activeForm"]
                        }
                    }
                },
                "required": ["items"],
            },
        },
    },
]


# Task tool - only available to main agent (not subagents)
TASK_TOOL = {
    "type": "function",
    "function": {
        "name": "run_task",
        "description": f"""Spawn a subagent for a focused subtask.

Subagents run in ISOLATED context - they don't see parent's history.
Use this to keep the main conversation clean.

Agent types:
{get_agent_descriptions()}

Example uses:
- run_task(explore): "Find all files using the auth module"
- run_task(plan): "Design a migration strategy for the database"
- run_task(code): "Implement the user registration form"
""",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Short task name (3-5 words) for progress display",
                },
                "prompt": {
                    "type": "string",
                    "description": "Detailed instructions for the subagent",
                },
                "agent_type": {
                    "type": "string",
                    "enum": ["explore", "code", "plan"],
                    "description": "Type of agent to spawn",
                },
            },
            "required": ["description", "prompt", "agent_type"],
        },
    },
}


# Skill tool - loads domain knowledge on-demand
# Note: description is set as placeholder to avoid circular import
# The actual descriptions are populated by get_skill_tool() when needed
_SKILL_TOOL_TEMPLATE = {
    "type": "function",
    "function": {
        "name": "run_skill",
        "description": "{skill_descriptions_placeholder}",
        "parameters": {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "Name of the skill to load",
                }
            },
            "required": ["skill_name"],
        },
    },
}


def get_skill_tool() -> dict:
    """Get the SKILL_TOOL with populated descriptions.

    This function is called lazily to avoid circular import issues.

    Returns:
        The complete SKILL_TOOL definition
    """
    descriptions = _get_skill_descriptions()
    tool = _SKILL_TOOL_TEMPLATE.copy()
    tool["function"]["description"] = tool["function"]["description"].format(
        skill_descriptions_placeholder=descriptions
    )
    return tool


# Alias for backward compatibility (evaluated lazily when first accessed)
class _LazySkillTool:
    """Lazy proxy for SKILL_TOOL."""
    def __init__(self):
        self._cached = None

    def __call__(self):
        if self._cached is None:
            self._cached = get_skill_tool()
        return self._cached


SKILL_TOOL = _LazySkillTool()


# All tools including Task and Skill tools (for main agent)
# Use lazy evaluation to avoid circular import
_ALL_TOOLS_CACHE = None


def get_all_tools() -> list:
    """Get all tools including Task and Skill tools.

    This resolves SKILL_TOOL lazily to avoid circular import.

    Returns:
        List of all tool definitions
    """
    global _ALL_TOOLS_CACHE
    if _ALL_TOOLS_CACHE is None:
        _ALL_TOOLS_CACHE = BASE_TOOLS + [TASK_TOOL, get_skill_tool()]
    return _ALL_TOOLS_CACHE


# Legacy alias for backward compatibility (only evaluates on access)
class _LegacyAllTools:
    """Lazy proxy for ALL_TOOLS."""
    def __iter__(self):
        return iter(get_all_tools())

    def __getitem__(self, key):
        return get_all_tools()[key]

    def __len__(self):
        return len(get_all_tools())


# Set ALL_TOOLS to a lazy proxy
ALL_TOOLS = _LegacyAllTools()
