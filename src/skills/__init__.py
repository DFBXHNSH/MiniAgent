# Skills module

from pathlib import Path
from .loader import SkillLoader

# Default skills directory
SKILLS_DIR = Path.cwd() / "skills"

# Global skill loader instance
SKILLS = SkillLoader(SKILLS_DIR)

__all__ = ["SkillLoader", "SKILLS", "SKILLS_DIR"]
