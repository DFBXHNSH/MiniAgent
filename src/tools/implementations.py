"""
Tool implementations for the agent.

This module provides the actual implementations of tools that the agent can call.
"""

import subprocess
import shutil
import platform
import re
from typing import Optional
from pathlib import Path

from src.tools.safety import safe_path
from src.tools.todo_manager import TODO

# Lazy import to avoid circular dependency
def _get_skills():
    from src.skills import SKILLS
    return SKILLS

# Bash executable path - cross-platform detection
def _find_bash_executable() -> str:
    """Find bash executable on the current platform."""
    # # First try to find bash in PATH
    # bash_path = shutil.which("bash")
    # if bash_path:
    #     return bash_path

    # Platform-specific fallbacks
    if platform.system() == "Windows":
        # Common Git Bash installation paths
        for path in [
            "E:\\Program Files\\Git\\Git\\bin\\bash.exe",
        ]:
            if Path(path).exists():
                # print("Found bash at", path)
                return path
        raise FileNotFoundError(
            "Bash not found. Please install Git for Windows or ensure bash is in PATH."
        )
    else:
        # Unix-like systems
        return "/bin/bash"

bash_exe = _find_bash_executable()


# Dangerous command patterns (regex for more precise matching)
_DANGEROUS_PATTERNS = [
    # Root deletion
    r"^\s*rm\s+-rf\s+/\s*",
    r"^\s*rm\s+-[a-zA-Z]*r\s+-[a-zA-Z]*f\s+/\s*",
    # System shutdown/reboot
    r"^\s*(sudo\s+)?(shutdown|reboot|halt|poweroff)\b",
    # User management
    r"^\s*(sudo\s+)?(userdel|groupdel)\s",
    r"^\s*(sudo\s+)?passwd\s+.*root",
    # Package removal
    r"^\s*(sudo\s+)?(apt-get\s+remove|apt\s+remove|yum\s+remove|dnf\s+remove)",
    # Service manipulation
    r"^\s*(sudo\s+)?systemctl\s+(stop|disable|mask)",
    # Disk wiping
    r"^\s*(sudo\s+)?dd\s+.*if=/dev/zero",
    r"^\s*(sudo\s+)?mkfs\.",
    # Dangerous redirections
    r">\s*/dev/",
    r">\s*/(proc|sys|dev)/",
    # History manipulation
    r"^\s*history\s+-c",
    # File permission changes to sensitive files
    r"^\s*chmod\s+777\s+/\s*",
    r"^\s*chmod\s+777\s+/etc/",
]


def _is_dangerous_command(command: str) -> tuple[bool, str]:
    """
    Check if a command contains dangerous patterns.

    Uses regex patterns for more precise matching of command starts.
    This prevents false positives from words that contain dangerous substrings.

    Args:
        command: The command to check

    Returns:
        A tuple of (is_dangerous, reason)
    """
    # Check against each dangerous pattern
    for pattern in _DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.MULTILINE):
            return True, f"Dangerous command pattern blocked: {pattern[:30]}"

    return False, ""


def bash(command: str) -> str:
    """
    Execute shell command with safety checks.

    Security: Blocks obviously dangerous commands using pattern matching.
    Timeout: 60 seconds to prevent hanging.
    Output: Truncated to 50KB to prevent context overflow.

    Args:
        command: The shell command to execute

    Returns:
        Command output or error message
    """
    # Enhanced safety check using regex patterns
    is_dangerous, reason = _is_dangerous_command(command)
    if is_dangerous:
        return f"Error: {reason}"

    try:
        result = subprocess.run(
            [bash_exe, "-c", command],
            cwd=safe_path("."),
            capture_output=True,
            text=True,
            timeout=60
        )
        output = (result.stdout + result.stderr).strip()
        return output[:50000] if output else "(no output)"

    except subprocess.TimeoutExpired:
        return "Error: Command timed out (60s)"
    except Exception as e:
        return f"Error: {e}"


def read_file(path: str, limit: Optional[int] = None) -> str:
    """
    Read file contents with optional line limit.

    For large files, use limit to read just the first N lines.
    Output truncated to 50KB to prevent context overflow.

    Args:
        path: The file path to read (relative to workspace)
        limit: Optional: Number of lines to read

    Returns:
        File contents or error message
    """
    try:
        text = safe_path(path).read_text()
        lines = text.splitlines()

        if limit and limit < len(lines):
            lines = lines[:limit]
            lines.append(f"... ({len(text.splitlines()) - limit} more lines)")

        return "\n".join(lines)[:50000]

    except Exception as e:
        return f"Error: {e}"


def write_file(path: str, content: str) -> str:
    """
    Write content to file, creating parent directories if needed.

    This is for complete file creation/overwrite.
    For partial edits, use edit_file instead.

    Args:
        path: The file path to write (relative to workspace)
        content: The content to write

    Returns:
        Success message or error message
    """
    try:
        fp = safe_path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
        return f"Wrote {len(content)} bytes to {path}"

    except Exception as e:
        return f"Error: {e}"


def edit_file(path: str, old_text: str, new_text: str) -> str:
    """
    Replace exact text in a file (surgical edit).

    Uses exact string matching - the old_text must appear verbatim.
    Only replaces the first occurrence to prevent accidental mass changes.

    Args:
        path: The file path to edit (relative to workspace)
        old_text: The exact text to replace
        new_text: The new text to replace with

    Returns:
        Success message or error message
    """
    try:
        fp = safe_path(path)
        content = fp.read_text()

        if old_text not in content:
            return f"Error: Text not found in {path}"

        # Replace only first occurrence for safety
        new_content = content.replace(old_text, new_text, 1)
        fp.write_text(new_content)
        return f"Edited {path}"

    except Exception as e:
        return f"Error: {e}"


def todo(items: list) -> str:
    """
    Update the todo list.

    The model sends a complete new list (not a diff).
    We validate it and return the rendered view.

    Args:
        items: List of todo items with content, status, activeForm

    Returns:
        Rendered todo list or error message
    """
    try:
        return TODO.update(items)
    except Exception as e:
        return f"Error: {e}"


# Task handler placeholder - set by agent module
_task_handler = None


def set_task_handler(handler):
    """Set the task handler function for spawning subagents."""
    global _task_handler
    _task_handler = handler


def run_task(description: str, prompt: str, agent_type: str) -> str:
    """
    Spawn a subagent to handle a subtask.

    The subagent runs in isolated context - it doesn't see the parent's history.
    The result is returned as a summary for the parent agent.

    Args:
        description: Short task name (3-5 words) for progress display
        prompt: Detailed instructions for the subagent
        agent_type: Type of agent to spawn (explore, code, plan)

    Returns:
        Summary of what the subagent accomplished
    """
    if _task_handler is None:
        return "Error: Task handler not initialized. Call set_task_handler() first."
    try:
        return _task_handler(description, prompt, agent_type)
    except Exception as e:
        return f"Error spawning subagent: {e}"


def run_skill(skill_name: str) -> str:
    """
    Load a skill and inject it into the conversation.

    This is the key mechanism for the Skills system:
    1. Get skill content (SKILL.md body + resource hints)
    2. Return it wrapped in <skill-loaded> tags
    3. Model receives this as tool_result (user message)
    4. Model now "knows" how to do the task

    Critical design: skill content goes into tool_result (user message),
    NOT system prompt. This preserves prompt cache!
    - System prompt changes invalidate cache (20-50x cost increase)
    - Tool results append to end (prefix unchanged, cache hit)

    Args:
        skill_name: Name of the skill to load

    Returns:
        Skill content wrapped in tags for model to follow
    """
    content = _get_skills().get_skill_content(skill_name)

    if content is None:
        available = ", ".join(_get_skills().list_skills()) or "none"
        return f"Error: Unknown skill '{skill_name}'. Available: {available}"

    # Wrap in tags so model knows it's skill content
    return f"""<skill-loaded name="{skill_name}">
{content}
</skill-loaded>

Follow the instructions in the skill above to complete the user's task."""
