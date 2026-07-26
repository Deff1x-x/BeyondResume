#!/bin/sh
# Backend container startup: migrate, seed ontology, then serve.
set -eu

echo "Running database migrations..."
alembic upgrade head

echo "Seeding Skill ontology..."
python -m app.scripts.seed_skill_ontology

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
