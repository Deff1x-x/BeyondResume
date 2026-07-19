from dataclasses import FrozenInstanceError, replace
import json

import pytest

from app.integrations.github import DemoGitHubProvider
from app.utils.github_manifests import (
    GitHubNormalizedDependency,
    InvalidManifestPathError,
    InvalidNormalizedDependencyError,
    normalize_fixture_manifests,
    normalize_manifest_path,
    parse_manifest,
)
from app.utils.github_snapshot import (
    GitHubSnapshotValidationError,
    UnsupportedGitHubSnapshotSchemaError,
    canonicalize_github_repository_snapshot,
    read_github_repository_snapshot_payload,
)
from app.utils.github_url import parse_github_repository_url


def test_manifest_path_normalization_and_rejection() -> None:
    assert normalize_manifest_path("nested\\package.json") == "nested/package.json"
    with pytest.raises(InvalidManifestPathError):
        normalize_manifest_path("../package.json")
    with pytest.raises(InvalidManifestPathError):
        normalize_manifest_path("/package.json")


@pytest.mark.parametrize(
    ("path", "content", "expected"),
    [
        ("package.json", '{"dependencies":{"React":"1"}}', "react"),
        ("pyproject.toml", '[project]\ndependencies=["Fast_API[all]>=1"]', "fast-api"),
        ("requirements.txt", "Django>=5\n", "django"),
        (
            "pom.xml",
            "<project><dependencies><dependency><groupId>org.X</groupId><artifactId>A</artifactId></dependency></dependencies></project>",
            "org.x:a",
        ),
        ("go.mod", "module x\nrequire example.com/Lib v1.0.0 // indirect", "example.com/lib"),
        ("Cargo.toml", "[dependencies]\nserde = '1'", "serde"),
        ("composer.json", '{"require":{"vendor/package":"1"}}', "vendor/package"),
        ("Gemfile", 'gem "rails"\n', "rails"),
        (
            "app.CSPROJ",
            '<Project><ItemGroup><PackageReference Include="Newtonsoft.Json" /></ItemGroup></Project>',
            "newtonsoft.json",
        ),
    ],
)
def test_each_allowed_manifest_parser_returns_normalized_dependency(
    path: str, content: str, expected: str
) -> None:
    dependencies, warnings = parse_manifest(path, content)

    assert warnings == ()
    assert dependencies[0].name == expected


def test_oversized_dependency_name_is_fatal() -> None:
    with pytest.raises(InvalidNormalizedDependencyError):
        parse_manifest("package.json", json.dumps({"dependencies": {"x" * 256: "1"}}))


def test_demo_provider_propagates_fatal_invalid_normalized_dependency(tmp_path) -> None:
    fixture = {
        "canonical_url": "https://github.com/demo-user/demo-api",
        "repository_name": "demo-api",
        "owner": "demo-user",
        "is_public": True,
        "languages": [],
        "file_tree": ["package.json"],
        "manifest_paths": ["package.json"],
        "manifest_contents": {"package.json": json.dumps({"dependencies": {"x" * 256: "1"}})},
    }
    (tmp_path / "demo-user--demo-api.json").write_text(json.dumps(fixture), encoding="utf-8")

    with pytest.raises(InvalidNormalizedDependencyError):
        DemoGitHubProvider(tmp_path).get_repository_snapshot(
            parse_github_repository_url("https://github.com/demo-user/demo-api")
        )


def test_demo_provider_returns_immutable_v2_snapshot_without_raw_contents() -> None:
    snapshot = DemoGitHubProvider().get_repository_snapshot(
        parse_github_repository_url("https://github.com/demo-user/demo-api")
    )

    assert snapshot.schema_version == 2
    assert snapshot.normalized_manifests[0].path == "pyproject.toml"
    with pytest.raises(FrozenInstanceError):
        snapshot.schema_version = 1  # type: ignore[misc]
    assert "dependencies =" not in canonicalize_github_repository_snapshot(snapshot).canonical_json


def test_v1_reader_is_compatible_and_v2_reader_rejects_future_schema() -> None:
    snapshot = DemoGitHubProvider().get_repository_snapshot(
        parse_github_repository_url("https://github.com/demo-user/demo-api")
    )
    v2_payload = json.loads(canonicalize_github_repository_snapshot(snapshot).canonical_json)
    v1_payload = {
        key: value
        for key, value in v2_payload.items()
        if key not in {"schema_version", "normalized_manifests", "manifest_warnings"}
    }

    historical = read_github_repository_snapshot_payload(v1_payload)
    assert historical.schema_version == 1
    assert historical.normalized_manifests == ()
    v2_payload["schema_version"] = 3
    with pytest.raises(UnsupportedGitHubSnapshotSchemaError):
        read_github_repository_snapshot_payload(v2_payload)


def test_normalization_deduplicates_dependencies_in_deterministic_order() -> None:
    manifests, warnings = normalize_fixture_manifests(
        ("package.json",),
        {"package.json": '{"dependencies":{"z":"1","a":"1"},"devDependencies":{"a":"2"}}'},
    )

    assert warnings == ()
    assert [(dependency.name, dependency.section) for dependency in manifests[0].dependencies] == [
        ("a", "dependencies"),
        ("a", "devDependencies"),
        ("z", "dependencies"),
    ]


def test_canonical_v2_serialization_sorts_checksum_relevant_collections() -> None:
    first = DemoGitHubProvider().get_repository_snapshot(
        parse_github_repository_url("https://github.com/demo-user/demo-api")
    )
    shuffled = replace(
        first,
        languages=tuple(reversed(first.languages)),
        file_tree=tuple(reversed(first.file_tree)),
        manifest_paths=tuple(reversed(first.manifest_paths)),
        normalized_manifests=tuple(reversed(first.normalized_manifests)),
        manifest_warnings=tuple(reversed(first.manifest_warnings)),
    )

    assert canonicalize_github_repository_snapshot(
        first
    ) == canonicalize_github_repository_snapshot(shuffled)


def test_dependency_metadata_is_deep_detached_from_caller_data() -> None:
    metadata: dict[str, object] = {"nested": {"values": ["before"]}}
    dependency = GitHubNormalizedDependency("name", None, metadata)
    metadata["nested"] = {"values": ["after"]}

    assert dependency.metadata["nested"] != metadata["nested"]
    with pytest.raises(TypeError):
        dependency.metadata["new"] = "value"  # type: ignore[index]


def test_pom_excludes_dependency_management_and_rejects_entities() -> None:
    dependencies, warnings = parse_manifest(
        "pom.xml",
        "<project><dependencyManagement><dependencies><dependency><groupId>x</groupId><artifactId>managed</artifactId></dependency></dependencies></dependencyManagement><dependencies><dependency><groupId>x</groupId><artifactId>direct</artifactId></dependency></dependencies></project>",
    )

    assert warnings == ()
    assert [dependency.name for dependency in dependencies] == ["x:direct"]
    _, warnings = parse_manifest("pom.xml", "<!DOCTYPE project [<!ENTITY x 'y'>]><project />")
    assert warnings[0].code == "malformed"


def test_reader_rejects_extra_nested_fields_and_non_json_metadata() -> None:
    snapshot = DemoGitHubProvider().get_repository_snapshot(
        parse_github_repository_url("https://github.com/demo-user/demo-api")
    )
    payload = json.loads(canonicalize_github_repository_snapshot(snapshot).canonical_json)
    payload["normalized_manifests"][0]["unexpected"] = True

    with pytest.raises(GitHubSnapshotValidationError):
        read_github_repository_snapshot_payload(payload)


@pytest.mark.parametrize("count", [50, 51])
def test_demo_provider_applies_manifest_processing_limit_without_rejecting_snapshot(
    tmp_path, count: int
) -> None:
    paths = [f"manifests/{index:03d}/package.json" for index in range(count)]
    fixture = {
        "canonical_url": "https://github.com/demo-user/demo-api",
        "repository_name": "demo-api",
        "owner": "demo-user",
        "is_public": True,
        "languages": [],
        "file_tree": paths,
        "manifest_paths": paths,
        "manifest_contents": {path: '{"dependencies":{}}' for path in paths},
    }
    (tmp_path / "demo-user--demo-api.json").write_text(json.dumps(fixture), encoding="utf-8")

    snapshot = DemoGitHubProvider(tmp_path).get_repository_snapshot(
        parse_github_repository_url("https://github.com/demo-user/demo-api")
    )

    assert len(snapshot.manifest_paths) == count
    assert len(snapshot.normalized_manifests) == min(count, 50)
    warnings = [
        warning
        for warning in snapshot.manifest_warnings
        if warning.code == "manifest_limit_exceeded"
    ]
    assert len(warnings) == (1 if count == 51 else 0)
    assert canonicalize_github_repository_snapshot(snapshot).payload["manifest_paths"]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload["normalized_manifests"][0].update({"path": "missing/package.json"}),
        lambda payload: payload["normalized_manifests"][0].update({"kind": "go_mod"}),
        lambda payload: payload["normalized_manifests"][0].update({"ecosystem": "go"}),
        lambda payload: payload["normalized_manifests"][0]["dependencies"][0]["metadata"].update(
            {"unknown": True}
        ),
        lambda payload: payload["normalized_manifests"][0]["dependencies"][0]["metadata"].update(
            {"group": 1}
        ),
    ],
)
def test_reader_rejects_inconsistent_manifest_identity_and_metadata(mutation) -> None:
    snapshot = DemoGitHubProvider().get_repository_snapshot(
        parse_github_repository_url("https://github.com/demo-user/demo-api")
    )
    payload = json.loads(canonicalize_github_repository_snapshot(snapshot).canonical_json)
    payload["normalized_manifests"][0]["dependencies"] = [
        {"name": "demo", "section": "project.dependencies", "metadata": {"group": None}}
    ]
    mutation(payload)

    with pytest.raises(GitHubSnapshotValidationError):
        read_github_repository_snapshot_payload(payload)
