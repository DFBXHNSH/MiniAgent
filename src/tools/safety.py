"""
Safety utilities for path validation.

This module ensures that file operations stay within the workspace.
"""

from pathlib import Path
from prompts.system import WORKDIR


def safe_path(p: str) -> Path:
    """
    Ensure path stays within workspace (security measure).

    Prevents the model from accessing files outside the project directory.
    Resolves relative paths and checks they don't escape via '../'.

    Args:
        p: The path string to validate

    Returns:
        A resolved Path object within the workspace

    Raises:
        ValueError: If the path attempts to escape the workspace
    """
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path
