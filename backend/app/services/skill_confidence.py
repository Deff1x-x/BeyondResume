"""Deterministic evidence-strength calculation for the Skill Passport."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, log1p
from typing import Iterable, Mapping, Sequence

from app.core.skill_confidence import (
    COVERAGE_SATURATION_PATHS,
    CROSS_REPOSITORY_SATURATION_REPOSITORIES,
    CROSS_REPOSITORY_WEIGHT,
    DIVERSITY_SATURATION_TYPES,
    EVIDENCE_DIVERSITY_WEIGHT,
    GITHUB_CONFIDENCE_CAP_PERCENT,
    PROJECT_COVERAGE_WEIGHT,
    QUALITY_SATURATION_ARTIFACTS,
    REPOSITORY_QUALITY_WEIGHT,
    SOURCE_USAGE_SIGNAL_STRENGTHS,
    SOURCE_USAGE_WEIGHT,
    WEAK_SIGNAL_TYPES,
)


@dataclass(frozen=True, slots=True)
class SkillEvidenceObservation:
    """The persisted data required to score one evidence-to-skill relation."""

    source_type: str
    source_reference: str | None
    quality_flags: Mapping[str, bool] | None
    context: Mapping[str, object] | None


@dataclass(frozen=True, slots=True)
class SkillConfidenceResult:
    confidence: float
    evidence_confidences: tuple[float, ...]


def calculate_skill_confidence(
    observations: Sequence[SkillEvidenceObservation],
) -> SkillConfidenceResult:
    """Score a skill from its persisted evidence without inferring new skills."""
    if not observations:
        return SkillConfidenceResult(confidence=0.0, evidence_confidences=())

    evidence_confidences = tuple(_score_observation(observation) for observation in observations)
    confidence = _confidence_from_factors(
        source_usage=_source_usage(observations),
        diversity=_diversity(observations),
        coverage=_coverage(observations),
        cross_repository=_cross_repository_confirmation(observations),
        repository_quality=_repository_quality(observations),
    )
    return SkillConfidenceResult(confidence=confidence, evidence_confidences=evidence_confidences)


def _score_observation(observation: SkillEvidenceObservation) -> float:
    return _confidence_from_factors(
        source_usage=_source_usage((observation,)),
        diversity=_diversity((observation,)),
        coverage=_coverage((observation,)),
        cross_repository=0.0,
        repository_quality=_repository_quality((observation,)),
    )


def _confidence_from_factors(
    *,
    source_usage: float,
    diversity: float,
    coverage: float,
    cross_repository: float,
    repository_quality: float,
) -> float:
    score = (
        source_usage * SOURCE_USAGE_WEIGHT
        + diversity * EVIDENCE_DIVERSITY_WEIGHT
        + coverage * PROJECT_COVERAGE_WEIGHT
        + cross_repository * CROSS_REPOSITORY_WEIGHT
        + repository_quality * REPOSITORY_QUALITY_WEIGHT
    )
    return round(min(max(score, 0.0), 1.0) * GITHUB_CONFIDENCE_CAP_PERCENT) / 100


def _source_usage(observations: Sequence[SkillEvidenceObservation]) -> float:
    strengths = [
        SOURCE_USAGE_SIGNAL_STRENGTHS.get(signal_type, 0.0)
        for signal_type in {
            signal_type for observation in observations for signal_type in _signal_types(observation)
        }
    ]
    return _saturating_union(strengths)


def _diversity(observations: Sequence[SkillEvidenceObservation]) -> float:
    kinds = {
        _signal_family(signal_type)
        for observation in observations
        for signal_type in _signal_types(observation)
    }
    kinds.discard("")
    return 1 - exp(-len(kinds) / DIVERSITY_SATURATION_TYPES) if kinds else 0.0


def _coverage(observations: Sequence[SkillEvidenceObservation]) -> float:
    paths = {
        path
        for observation in observations
        for path in _signal_paths(observation)
        if path
    }
    return min(log1p(len(paths)) / log1p(COVERAGE_SATURATION_PATHS), 1.0) if paths else 0.0


def _cross_repository_confirmation(observations: Sequence[SkillEvidenceObservation]) -> float:
    repositories = {
        observation.source_reference
        for observation in observations
        if observation.source_type == "github_repository" and observation.source_reference
    }
    additional_repositories = max(len(repositories) - 1, 0)
    return 1 - exp(-additional_repositories / CROSS_REPOSITORY_SATURATION_REPOSITORIES)


def _repository_quality(observations: Sequence[SkillEvidenceObservation]) -> float:
    artifacts: set[str] = set()
    for observation in observations:
        flags = observation.quality_flags or {}
        if observation.source_type == "github_repository":
            if flags.get("missing_readme") is False:
                artifacts.add("readme")
            if flags.get("empty_file_tree") is False:
                artifacts.add("source_tree")
            if flags.get("missing_manifests") is False:
                artifacts.add("manifest")
        artifacts.update(
            signal_type
            for signal_type in _signal_types(observation)
            if signal_type in {"test_usage", "ci", "docker"}
        )
    return 1 - exp(-len(artifacts) / QUALITY_SATURATION_ARTIFACTS) if artifacts else 0.0


def _signal_types(observation: SkillEvidenceObservation) -> tuple[str, ...]:
    signals = (observation.context or {}).get("signals")
    if not isinstance(signals, list):
        return ()
    result: list[str] = []
    for signal in signals:
        if not isinstance(signal, Mapping):
            continue
        value = signal.get("type")
        if isinstance(value, str):
            result.append(value.strip().lower())
    return tuple(result)


def _signal_paths(observation: SkillEvidenceObservation) -> tuple[str, ...]:
    signals = (observation.context or {}).get("signals")
    if not isinstance(signals, list):
        return ()
    paths: list[str] = []
    for signal in signals:
        if not isinstance(signal, Mapping):
            continue
        signal_type = signal.get("type")
        if not isinstance(signal_type, str) or signal_type.strip().lower() == "readme":
            continue
        for key in ("path", "manifest", "file"):
            value = signal.get(key)
            if isinstance(value, str) and value.strip():
                paths.append(value.strip())
                break
    return tuple(paths)


def _signal_family(signal_type: str) -> str:
    if signal_type in WEAK_SIGNAL_TYPES:
        return signal_type
    if signal_type.startswith("source_"):
        return "source_code"
    if signal_type == "test_usage":
        return "tests"
    return signal_type


def _saturating_union(strengths: Iterable[float]) -> float:
    remaining = 1.0
    for strength in strengths:
        remaining *= 1 - min(max(strength, 0.0), 1.0)
    return 1 - remaining
