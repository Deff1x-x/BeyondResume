from app.services.skill_confidence import SkillEvidenceObservation, calculate_skill_confidence


def observation(
    *signals: dict[str, str],
    repository: str = "https://github.com/demo/repository",
    quality: dict[str, bool] | None = None,
) -> SkillEvidenceObservation:
    return SkillEvidenceObservation(
        source_type="github_repository",
        source_reference=repository,
        quality_flags=quality,
        context={"signals": list(signals)},
    )


def test_dependency_manifest_alone_is_weak_evidence() -> None:
    result = calculate_skill_confidence(
        (observation({"type": "dependency_manifest", "manifest": "package.json"}),)
    )

    assert 0 < result.confidence < 0.2
    assert result.evidence_confidences == (result.confidence,)


def test_real_code_usage_diversity_coverage_and_quality_raise_confidence_below_cap() -> None:
    quality = {
        "missing_readme": False,
        "empty_file_tree": False,
        "missing_manifests": False,
    }
    result = calculate_skill_confidence(
        (
            observation(
                {"type": "source_import", "path": "app/main.py"},
                {"type": "source_api_call", "path": "app/routes.py"},
                {"type": "test_usage", "path": "tests/test_api.py"},
                {"type": "ci", "path": ".github/workflows/tests.yml"},
                {"type": "docker", "path": "Dockerfile"},
                quality=quality,
            ),
        )
    )

    assert result.confidence > 0.7
    assert result.confidence <= 0.95


def test_cross_repository_confirmation_is_bounded_and_non_linear() -> None:
    first = observation({"type": "source_import", "path": "app/main.py"})
    second = observation(
        {"type": "source_import", "path": "src/main.py"}, repository="https://github.com/demo/other"
    )
    third = observation(
        {"type": "source_import", "path": "service/main.py"}, repository="https://github.com/demo/third"
    )
    one = calculate_skill_confidence((first,)).confidence
    two = calculate_skill_confidence((first, second)).confidence
    three = calculate_skill_confidence((first, second, third)).confidence

    assert one < two < three <= 0.95
    assert three - two <= two - one


def test_project_coverage_has_diminishing_returns() -> None:
    one_path = calculate_skill_confidence(
        tuple(
            observation({"type": "source_function_usage", "path": f"app/{index}.py"})
            for index in range(1)
        )
    ).confidence
    two_paths = calculate_skill_confidence(
        tuple(
            observation({"type": "source_function_usage", "path": f"app/{index}.py"})
            for index in range(2)
        )
    ).confidence
    three_paths = calculate_skill_confidence(
        tuple(
            observation({"type": "source_function_usage", "path": f"app/{index}.py"})
            for index in range(3)
        )
    ).confidence

    assert one_path < two_paths < three_paths <= 0.95
    assert three_paths - two_paths < two_paths - one_path


def test_calculation_is_reproducible_and_never_exceeds_github_cap() -> None:
    signals = tuple(
        {"type": "source_api_call", "path": f"app/{index}.py"} for index in range(30)
    )
    observations = tuple(
        observation(*signals, repository=f"https://github.com/demo/{index}") for index in range(6)
    )

    first = calculate_skill_confidence(observations)
    second = calculate_skill_confidence(observations)

    assert first == second
    assert first.confidence <= 0.95
