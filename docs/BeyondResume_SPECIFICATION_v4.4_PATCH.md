# BeyondResume Specification v4.4 Patch

## Status, scope, and precedence

This is a normative patch for GitHub deterministic re-extraction and
reconciliation after accepted Stage 9.9B. It overrides v4.3 and v4.2 only
within this scope; all other requirements remain unchanged.

## Existing accepted boundaries

The following contracts remain their sole owners and MUST NOT be reimplemented:

- `read_github_repository_snapshot_payload(...)` reads persisted V1/V2 payloads;
- `extract_github_skill_candidates(...)` performs pure dependency-manifest extraction;
- `resolve_github_skill_candidates(...)` performs ontology resolution;
- `build_github_evidence_commands(...)` is the only aggregation boundary;
- `build_github_skill_link_values(...)` copies command fields without semantic transformation;
- `persist_github_evidence_skill_link(...)` is the v4.3 serialization and single-link persistence boundary;
- `persist_resolved_github_skill_candidates(...)` is the only command → builder → adapter iterator.

No new layer MAY change matching, rule IDs, extraction version, confidence,
command context, aggregation, EvidenceSkillLink identity, or the existing
tuple-return contracts of `extract_github_skill_candidates(...)` and
`resolve_github_skill_candidates(...)`.

## Separate application stage and public contract

`run_github_repository_scan(...)` and Stage 7 orchestration MUST NOT change.
Deterministic re-extraction is a separate explicit application use case, invoked
by a subsequent caller after successful snapshot persistence and EvidenceUnit
generation. It MUST NOT use a provider, network, filesystem, or raw live data.

The canonical public entry point is:

```python
def reextract_github_evidence_skills(
    session: Session,
    *,
    candidate_id: UUID,
    github_repository_id: UUID,
    evidence_unit_id: UUID,
) -> GitHubSkillExtractionResult: ...
```

The caller owns the transaction.

## Loads and source consistency

`reextract_github_evidence_skills(...)` MUST load exactly:

1. `CandidateProfile` by `candidate_id`;
2. `GitHubRepository` by `github_repository_id`;
3. the current `GitHubRepositorySnapshot` belonging to that repository;
4. `EvidenceUnit` by `evidence_unit_id`.

Before any mutation it MUST fail fast as follows:

- missing candidate: `CandidateProfileNotFoundError`;
- missing repository: `GitHubRepositorySourceNotFoundError`;
- missing snapshot: `GitHubRepositorySnapshotNotFoundError`;
- missing EvidenceUnit: `EvidenceUnitNotFoundError`;
- repository/EvidenceUnit candidate mismatch, invalid EvidenceUnit `source_type`,
  or EvidenceUnit `source_reference` unequal to the canonical repository URL:
  `GitHubEvidenceSourceConsistencyError`;
- snapshot `repository_id` mismatch, or persisted canonical URL/owner/repository
  name mismatch: existing `GitHubSnapshotIdentityMismatchError`.

`GitHubEvidenceSourceConsistencyError` is a new typed application-domain error
only for the source-consistency cases in this section. It MUST NOT replace
`EvidenceSkillLinkCandidateMismatchError`, which remains owned by command
factory and single-link persistence validation.

The application use case MUST read the stored payload only through
`read_github_repository_snapshot_payload(...)`. V1 has no manifest candidates;
V2 is the sole dependency-manifest source. It MUST NOT parse manifests,
revalidate payload schema, or normalize provider data.

## Pipeline order

After all loads and consistency validation succeed, the use case MUST:

1. read the persisted snapshot DTO;
2. run the Stage 9.10A companion pure GitHub extraction result function;
3. retain unmatched manifest signals;
4. resolve candidates through the existing resolution layer;
5. retain unresolved rule targets;
6. call `reconcile_github_evidence_skill_links(...)` with every resolved candidate;
7. return `GitHubSkillExtractionResult`.

It MUST NOT aggregate signals, construct commands or values, deep-thaw context,
upsert one link, calculate confidence, or create a Skill.

## Unresolved contracts

Current extraction/resolution functions do not expose the unresolved collections
required by v4.2 §17.5. Stage 9.10A MUST add these canonical immutable types:

```python
@dataclass(frozen=True, slots=True)
class GitHubUnmatchedManifestSignal:
    signal_type: str
    source_manifest: str
    manifest_kind: str
    ecosystem: str
    source_dependency: str

@dataclass(frozen=True, slots=True)
class GitHubSkillCandidateExtractionResult:
    candidates: tuple[GitHubSkillCandidate, ...]
    unmatched_signals: tuple[GitHubUnmatchedManifestSignal, ...]

@dataclass(frozen=True, slots=True)
class GitHubSkillCandidateResolutionResult:
    resolved_candidates: tuple[ResolvedGitHubSkillCandidate, ...]
    unresolved_rule_targets: tuple[GitHubSkillCandidate, ...]
```

Stage 9.10A MUST add these companion pure functions:

```python
def extract_github_skill_candidate_extraction_result(
    snapshot: GitHubRepositorySnapshot,
    *,
    rules: tuple[GitHubDeterministicSkillRule, ...],
) -> GitHubSkillCandidateExtractionResult: ...

def resolve_github_skill_candidate_resolution_result(
    session: Session,
    candidates: Sequence[GitHubSkillCandidate],
) -> GitHubSkillCandidateResolutionResult: ...
```

The existing `extract_github_skill_candidates(...)` and
`resolve_github_skill_candidates(...)` public contracts MUST remain unchanged.
The companion extraction function is the only Stage 9.10A component authorized
to classify normalized dependency-manifest signals as matched or unmatched; the
companion resolution function is the only component authorized to classify a
matched candidate as resolved or unresolved.

`GitHubUnmatchedManifestSignal` is a normalized dependency-manifest signal for
which exact rule lookup returned `None`. `GitHubSkillCandidate` is an unresolved
rule target when its `target_skill_name` did not resolve through `resolve_skill`.
Both collections MUST be deterministically sorted by their source-signal fields,
MUST NOT persist data, and MUST NOT protect an absent resolved identity from
stale deletion.

## Reconciliation contract

The canonical reconciliation entry point is:

```python
def reconcile_github_evidence_skill_links(
    session: Session,
    *,
    candidate_id: UUID,
    evidence_unit: EvidenceUnit,
    resolved_candidates: Sequence[ResolvedGitHubSkillCandidate],
) -> GitHubEvidenceSkillLinkReconciliationResult: ...
```

It MUST call `persist_resolved_github_skill_candidates(...)` exactly once and
MUST NOT reimplement factory aggregation, builder mapping, deep-thaw, or
single-link upsert behavior.

Before that call it MUST load existing links only in the strict stale scope.
The ordered Stage 9.9B `persistence_results` are the complete desired identity
set and final desired links. Reconciliation MUST delete every scoped existing
link absent from that set with `session.delete(...)`.

## Strict stale scope and identity

The existing-link query and stale deletion scope MUST include all of:

- `EvidenceSkillLink.evidence_unit_id == evidence_unit.id`;
- `EvidenceSkillLink.candidate_id == candidate_id`;
- `EvidenceSkillLink.extraction_method == GITHUB_DETERMINISTIC_EXTRACTION_METHOD`;
- `EvidenceSkillLink.extraction_version == GITHUB_DETERMINISTIC_EXTRACTION_VERSION`.

Method and version MUST use the existing constants exported by
`github_evidence_commands`; reconciliation code MUST NOT use string literals.

Desired/existing membership uses only:

```text
(evidence_unit_id, skill_id, extraction_method, extraction_version)
```

Context and confidence are mutable fields, not identity. A matching identity
with changed mutable fields MUST be updated by accepted persistence, never
deleted and recreated. Reconciliation MUST NOT affect manual, AI,
other-version, other-EvidenceUnit, other-candidate, or other-provider links.
An empty resolved desired set is authoritative and deletes all links only inside
this strict scope.

## Immutable results and counters

```python
@dataclass(frozen=True, slots=True)
class GitHubEvidenceSkillLinkReconciliationResult:
    links: tuple[EvidenceSkillLink, ...]
    created_count: int
    changed_count: int
    unchanged_count: int
    removed_count: int

@dataclass(frozen=True, slots=True)
class GitHubSkillExtractionResult:
    evidence_unit: EvidenceUnit
    extraction_version: str
    links: tuple[EvidenceSkillLink, ...]
    created_count: int
    changed_count: int
    unchanged_count: int
    removed_count: int
    unmatched_signals: tuple[GitHubUnmatchedManifestSignal, ...]
    unresolved_rule_targets: tuple[GitHubSkillCandidate, ...]
```

Reconciliation `links` contains final desired active links in exact factory
order, never stale deleted links. Each desired persistence result contributes to
exactly one counter: `created=True, changed=True` increments `created_count`;
`created=False, changed=True` increments `changed_count`; and
`created=False, changed=False` increments `unchanged_count`. `removed_count`
equals scoped stale links passed to `session.delete`. Final result links and
counters are copied directly from reconciliation. Its version MUST equal
`GITHUB_DETERMINISTIC_EXTRACTION_VERSION`.

## Mutation, idempotency, transaction, and errors

The deterministic order is:

1. complete loads, validation, persisted-snapshot reading, extraction, and resolution;
2. load existing strict-scope links;
3. upsert the complete desired set through Stage 9.9B in factory order;
4. delete stale links ordered by `str(skill_id)` ascending.

No mutation MAY begin before the complete authoritative desired set exists.
Application and reconciliation layers MUST NOT flush, commit, rollback, retry,
or open a nested transaction. Existing single-link persistence flushes remain
unchanged. `session.delete` remains pending for the caller-owned transaction.
All typed errors, SQLAlchemy errors, and `IntegrityError` propagate unchanged;
no failure becomes partial success.

For identical stored snapshot and database state, a repeated call MUST report
`created_count == 0`, `changed_count == 0`, `removed_count == 0`, and count all
desired links as unchanged. A disappeared resolved identity is deleted only in
strict scope and increments `removed_count`.

## Forbidden behavior

Implementations MUST NOT modify Stage 7, call providers/network/filesystem/raw
payloads, alter snapshot schema or EvidenceSkillLink identity, aggregate outside
command factory, deep-thaw outside the v4.3 adapter, auto-create ontology data,
hide transaction control or `IntegrityError`, or add API, jobs, migrations, or
provider integration in the same stage.

## Implementation order

1. **Stage 9.10A — Unresolved result contracts and typed application errors.**
   Add the immutable unresolved contracts and companion pure functions above,
   without changing accepted extractor/resolver contracts. No database mutation
   or Stage 7 integration.
2. **Stage 9.10B — Scoped GitHub deterministic reconciliation.** Add the
   reconciliation result and service, reusing Stage 9.9B exactly once, scoped
   existing-link loading, deterministic stale deletion, and no transaction control.
3. **Stage 9.10C — Persisted-snapshot application re-extraction.** Add final
   result composition, required loads, source validation, reader, extraction,
   resolution, and reconciliation.
4. **Stage 9.10D — Explicit caller/trigger.** Prohibited until a later patch
   explicitly defines its caller and trigger; it MUST NOT implicitly modify Stage 7.

## Acceptance criteria

Tests MUST prove pre-mutation source failures, V1 authoritative empty desired
set, V2 normalized-manifest-only extraction, factory-only aggregation,
adapter-only deep-thaw, strict-scope deletion, deterministic links/counters,
idempotency, unresolved-result preservation, and absence of application-layer
transaction control. Stage 7, provider, API, jobs, ORM schema, and migrations
MUST remain unchanged.

## Explicit non-goals

This patch does not authorize Stage 7 integration, API routes, background jobs,
Passport rebuild/scoring, other providers, production rule catalog entries,
migrations, or changes outside the Stage 9.10 sequence defined here.

Within this patch's narrow scope, deterministic re-extraction is limited to the
accepted dependency-manifest pipeline. Repository-language extraction is
explicitly deferred and MUST NOT be added in Stage 9.10A–9.10D. This limited
scope has priority over the broader repository-language wording in v4.2 §17.5.
