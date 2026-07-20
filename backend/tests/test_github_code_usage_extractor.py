from app.integrations.github import GitHubRepositorySnapshot
from app.services.skill_confidence import SkillEvidenceObservation, calculate_skill_confidence
from app.utils.github_skill_extractor import extract_github_skill_candidates


def snapshot(*files: tuple[str, str]) -> GitHubRepositorySnapshot:
    return GitHubRepositorySnapshot(
        canonical_url="https://github.com/demo/project",
        repository_name="project",
        owner="demo",
        description=None,
        default_branch="main",
        is_public=True,
        is_archived=False,
        languages=("Python", "TypeScript"),
        file_tree=tuple(path for path, _ in files),
        readme_text="# Demo",
        manifest_paths=(),
        is_demo=True,
        source_files=files,
    )


def signals_for(candidates, skill: str) -> set[str]:
    return {candidate.signal_type for candidate in candidates if candidate.target_skill_name == skill}


def test_extracts_import_api_class_test_config_docker_and_ci_usage() -> None:
    candidates = extract_github_skill_candidates(
        snapshot(
            ("app/main.py", "from fastapi import FastAPI, APIRouter\nfrom sqlalchemy.orm import Session\napp = FastAPI()\nrouter = APIRouter()\n"),
            ("tests/test_main.py", "import pytest\nfrom fastapi.testclient import TestClient\n@pytest.fixture\ndef client(): pass\n"),
            ("pytest.ini", "[pytest]\n"),
            ("Dockerfile", "FROM python:3.12\n"),
            ("docker-compose.yml", "services: {}\n"),
            (".github/workflows/test.yml", "steps:\n  - run: pytest\n  - run: docker build .\n"),
        )
    )

    assert {"source_import", "source_api_call"} <= signals_for(candidates, "FastAPI")
    assert "source_class_usage" in signals_for(candidates, "SQLAlchemy")
    assert "test_usage" in signals_for(candidates, "Pytest")
    assert "configuration_usage" in signals_for(candidates, "Pytest")
    assert "docker" in signals_for(candidates, "Docker")
    assert "ci" in signals_for(candidates, "Docker")
    assert "ci" in signals_for(candidates, "GitHub Actions")


def test_excludes_lock_generated_vendor_and_minified_files() -> None:
    candidates = extract_github_skill_candidates(
        snapshot(
            ("node_modules/react/index.js", "import React from 'react'"),
            ("vendor/app.py", "from fastapi import FastAPI"),
            ("generated/client.py", "from fastapi import FastAPI"),
            ("package-lock.json", "react"),
            ("src/app.min.js", "import React from 'react'"),
        )
    )

    assert candidates == ()


def test_source_signals_are_deduplicated_ordered_and_raise_confidence() -> None:
    files = (
        ("src/a.tsx", "import React from 'react'; useState(0)"),
        ("src/b.tsx", "import React from 'react'; useEffect(() => {})"),
        ("tests/app.test.tsx", "import React from 'react'; useState(0)"),
    )
    first = extract_github_skill_candidates(snapshot(*files))
    second = extract_github_skill_candidates(snapshot(*reversed(files)))
    react = [candidate for candidate in first if candidate.target_skill_name == "React"]

    assert first == second
    assert {candidate.source_manifest for candidate in react} == {
        "src/a.tsx",
        "src/b.tsx",
        "tests/app.test.tsx",
    }
    assert len({(candidate.signal_type, candidate.source_manifest) for candidate in react}) == len(react)
    weak = calculate_skill_confidence((SkillEvidenceObservation("github_repository", "https://github.com/demo/project", None, {"signals": [{"type": "dependency_manifest", "manifest": "package.json"}]}),)).confidence
    strong = calculate_skill_confidence((SkillEvidenceObservation("github_repository", "https://github.com/demo/project", {"missing_readme": False, "empty_file_tree": False, "missing_manifests": False}, {"signals": [{"type": item.signal_type, "manifest": item.source_manifest} for item in react]}),)).confidence
    assert weak < strong <= 0.95
