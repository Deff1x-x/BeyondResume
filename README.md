    # BeyondResume

## Purpose

BeyondResume is a hackathon MVP for evidence-based hiring of Junior IT specialists.

## Structure

```text
frontend/   Next.js application
backend/    FastAPI application
fixtures/   Project fixtures
infra/      Docker infrastructure
docs/       Project specification
```

## Start


```bash
docker compose up
```

## Skill ontology

Initialize the baseline deterministic skill ontology once after the database schema is ready:

```bash
cd backend
python -m app.scripts.seed_skill_ontology
```

The command is idempotent: it creates missing canonical skills and aliases without
changing existing ontology rows. After seeding, run GitHub analysis again to
reconcile deterministic EvidenceSkillLinks for an already connected repository.
