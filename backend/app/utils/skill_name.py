import re
import unicodedata


class InvalidSkillNameError(ValueError):
    """Raised when a skill name has no normalized value."""


def normalize_skill_name(value: str) -> str:
    if not isinstance(value, str):
        raise InvalidSkillNameError("Skill name must be a string")
    normalized = value.strip()
    normalized = unicodedata.normalize("NFKC", normalized).lower()
    normalized = normalized.replace("_", " ").replace("-", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized:
        raise InvalidSkillNameError("Skill name must not be empty")
    return normalized
