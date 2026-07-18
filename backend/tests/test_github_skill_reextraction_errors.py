from inspect import getsource

from app.services.github_skill_reextraction_errors import GitHubEvidenceSourceConsistencyError
from app.services.github_scan import GitHubSnapshotIdentityMismatchError
import app.services.github_skill_reextraction_errors as errors_module


def test_source_consistency_uses_one_typed_boundary_error() -> None:
    error = GitHubEvidenceSourceConsistencyError("repository candidate mismatch")

    assert isinstance(error, Exception)
    assert str(error) == "repository candidate mismatch"
    assert (
        errors_module.GitHubEvidenceSourceConsistencyError is GitHubEvidenceSourceConsistencyError
    )


def test_snapshot_identity_error_remains_a_separate_existing_type() -> None:
    assert GitHubSnapshotIdentityMismatchError is not GitHubEvidenceSourceConsistencyError
    assert isinstance(GitHubSnapshotIdentityMismatchError(), Exception)


def test_error_module_has_no_session_sql_or_lookup_behavior() -> None:
    source = getsource(errors_module)
    assert "Session" not in source
    assert "select" not in source
    assert ".execute(" not in source
    assert ".commit(" not in source
    assert ".rollback(" not in source
