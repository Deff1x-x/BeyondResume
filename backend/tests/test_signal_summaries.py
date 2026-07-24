import pytest

from app.services.signal_summaries import (
    public_categories_for_evidence,
    public_categories_from_contexts,
    public_categories_from_signal_types,
)


def test_duplicate_signals_collapse_to_one_category() -> None:
    assert public_categories_from_signal_types(
        ["dependency_manifest", "dependency_manifest", "docker"]
    ) == ("project_dependencies", "container_configuration")


def test_multiple_source_types_collapse_to_source_code_usage() -> None:
    assert public_categories_from_signal_types(
        ["source_import", "source_api_call", "source_function_usage", "source_class_usage"]
    ) == ("source_code_usage",)


def test_mixed_github_signal_set_is_deduplicated_and_ordered() -> None:
    assert public_categories_from_signal_types(
        [
            "ci",
            "docker",
            "source_import",
            "dependency_manifest",
            "test_usage",
            "configuration_usage",
            "dependency_manifest",
        ]
    ) == (
        "project_dependencies",
        "source_code_usage",
        "test_usage",
        "application_configuration",
        "container_configuration",
        "ci_cd_configuration",
    )


def test_test_usage_is_separate_from_source_code() -> None:
    assert public_categories_from_signal_types(["source_import", "test_usage"]) == (
        "source_code_usage",
        "test_usage",
    )


def test_reserved_source_logic_maps_to_source_code_usage() -> None:
    assert public_categories_from_signal_types(["source_logic"]) == ("source_code_usage",)


def test_package_manifest_and_lockfile_map_to_project_dependencies() -> None:
    assert public_categories_from_signal_types(["package_manifest", "lockfile"]) == (
        "project_dependencies",
    )


def test_readme_is_ignored() -> None:
    assert public_categories_from_signal_types(["readme", "docker"]) == ("container_configuration",)


def test_unknown_signal_is_ignored() -> None:
    assert public_categories_from_signal_types(["future_signal_x", "dependency_manifest"]) == (
        "project_dependencies",
    )


@pytest.mark.parametrize(
    "contexts",
    [
        None,
        [None],
        [{}],
        [{"signals": "not-a-list"}],
        [{"signals": ["not-a-dict"]}],
        [{"signals": [{"matched_value": "x"}]}],
        [{"signals": [{"type": 123}]}],
    ],
)
def test_malformed_contexts_do_not_raise(contexts: object) -> None:
    assert public_categories_from_contexts(contexts) == ()  # type: ignore[arg-type]


def test_resume_source_type_yields_resume_evidence_without_context() -> None:
    assert public_categories_for_evidence(source_type="resume", contexts=()) == ("resume_evidence",)
    assert public_categories_for_evidence(
        source_type="resume",
        contexts=[
            {
                "extractor": "evidence_skill_v1",
                "matched_term": "Python",
                "match_kind": "alias",
                "signals": [{"type": "dependency_manifest"}],
            }
        ],
    ) == ("resume_evidence",)


def test_github_without_signals_yields_empty() -> None:
    assert (
        public_categories_for_evidence(
            source_type="github_repository",
            contexts=[{"extractor": "evidence_skill_v1", "matched_term": "Python"}],
        )
        == ()
    )
