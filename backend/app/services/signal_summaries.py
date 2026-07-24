"""Map internal EvidenceSkillLink signal types to employer-safe public categories.

Pure functions only: no Session, no Pydantic, no I/O.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

# Stable public vocabulary for nested matched evidence.
PUBLIC_CATEGORY_ORDER: tuple[str, ...] = (
    "resume_evidence",
    "project_dependencies",
    "source_code_usage",
    "test_usage",
    "application_configuration",
    "container_configuration",
    "ci_cd_configuration",
)

# Allowlisted internal → public mapping. Unmapped types are ignored.
_INTERNAL_SIGNAL_TO_CATEGORY: dict[str, str] = {
    "dependency_manifest": "project_dependencies",
    "package_manifest": "project_dependencies",
    "lockfile": "project_dependencies",
    "source_import": "source_code_usage",
    "source_api_call": "source_code_usage",
    "source_class_usage": "source_code_usage",
    "source_function_usage": "source_code_usage",
    "source_logic": "source_code_usage",
    "test_usage": "test_usage",
    "configuration_usage": "application_configuration",
    "docker": "container_configuration",
    "ci": "ci_cd_configuration",
    # "readme" intentionally omitted — ignored.
}

RESUME_SOURCE_TYPE = "resume"
RESUME_EVIDENCE_CATEGORY = "resume_evidence"


def public_categories_for_evidence(
    *,
    source_type: str,
    contexts: Sequence[Mapping[str, Any] | None] | None = None,
) -> tuple[str, ...]:
    """Return deduplicated, ordered public categories for one skill↔evidence pair.

    Resume evidence always yields ``resume_evidence`` from ``source_type`` alone.
    GitHub (and other) units derive categories only from ``context.signals``.
    """
    if source_type == RESUME_SOURCE_TYPE:
        return (RESUME_EVIDENCE_CATEGORY,)
    return public_categories_from_contexts(contexts or ())


def public_categories_from_contexts(
    contexts: Sequence[Mapping[str, Any] | None] | None,
) -> tuple[str, ...]:
    """Collapse signal types from one or more link contexts into public categories."""
    return public_categories_from_signal_types(_signal_types_from_contexts(contexts or ()))


def public_categories_from_signal_types(signal_types: Iterable[object]) -> tuple[str, ...]:
    """Map internal signal type strings to a stable ordered public category tuple."""
    found: set[str] = set()
    for signal_type in signal_types:
        if not isinstance(signal_type, str):
            continue
        category = _INTERNAL_SIGNAL_TO_CATEGORY.get(signal_type)
        if category is not None:
            found.add(category)
    return tuple(category for category in PUBLIC_CATEGORY_ORDER if category in found)


def _signal_types_from_contexts(
    contexts: Sequence[Mapping[str, Any] | None],
) -> list[object]:
    types: list[object] = []
    for context in contexts:
        if not isinstance(context, Mapping):
            continue
        signals = context.get("signals")
        if not isinstance(signals, list):
            continue
        for signal in signals:
            if not isinstance(signal, Mapping):
                continue
            types.append(signal.get("type"))
    return types
