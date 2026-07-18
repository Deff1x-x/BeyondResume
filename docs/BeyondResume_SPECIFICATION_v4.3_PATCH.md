# BeyondResume Specification v4.3 Patch

## Patch
**Version:** 4.3  
**Date:** 2026-07-19

---

# §17.5 — Persistence serialization boundary

`GitHubEvidenceCommand.context` and
`GitHubEvidenceSkillLinkValues.context` use the canonical deeply immutable
application representation defined by this section.

The GitHub persistence adapter is the only boundary permitted to convert this
immutable representation into the mutable JSON-compatible representation
required by `persist_evidence_skill_link()` and the ORM JSON field.

This conversion is a representation-only transformation and is **not** a
semantic transformation.

The adapter **MUST** perform a deterministic recursive deep-thaw using only the
following conversions:

- `Mapping[str, object]` → `dict[str, object]`;
- `tuple[object, ...]` → `list[object]`;
- nested mappings and tuples **MUST** be converted recursively;
- JSON scalar values (`str`, `int`, `bool`, `None`, and `Decimal` only where
  already accepted by the persistence contract) **MUST** retain both their
  values and types.

For the canonical GitHub deterministic context defined by this specification,
all persisted values **MUST** be JSON-serializable after deep-thaw.

The conversion **MUST NOT**:

- add, remove, rename, or reorder context keys;
- add, remove, reorder, merge, or deduplicate signals;
- change scalar values;
- mutate the source command;
- mutate the values DTO;
- mutate the immutable context;
- mutate the signals collection;
- mutate individual signal mappings;
- perform persistence;
- perform lookup;
- perform skill resolution;
- perform aggregation;
- evaluate business rules;
- use `str()`, `repr()`, or any other lossy fallback for unsupported values.

Unsupported value types **MUST** be rejected fail-fast using the project's
typed extraction-context validation error.

The resulting mutable `dict[str, object]` is then passed to the existing
`persist_evidence_skill_link()` service.

`persist_evidence_skill_link()` and its current public contract remain
unchanged.

---

## Architectural clarification

The serialization boundary exists **only** inside the GitHub persistence
adapter.

The architecture therefore becomes:

```text
GitHubEvidenceCommand
        │
        ▼
GitHubEvidenceSkillLinkValues
        │
        ▼
GitHub Persistence Adapter
        │
        ├── deterministic deep-thaw
        ▼
persist_evidence_skill_link()
        ▼
EvidenceSkillLink
```

Neither the command factory nor the builder may perform mutable conversion.

Only the persistence adapter is allowed to convert immutable application
representations into mutable JSON-compatible structures required by the
existing persistence layer.
