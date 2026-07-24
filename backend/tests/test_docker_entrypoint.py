"""Deployment contract for the backend container startup script."""

from __future__ import annotations

from pathlib import Path

_ENTRYPOINT = Path(__file__).resolve().parents[1] / "docker-entrypoint.sh"


def _active_commands(script: str) -> list[str]:
    commands: list[str] = []
    for raw in script.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        commands.append(stripped)
    return commands


def test_docker_entrypoint_runs_migrations_seed_then_exec_uvicorn() -> None:
    raw = _ENTRYPOINT.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in raw
    assert b"\r" not in raw

    script = raw.decode("utf-8")
    commands = _active_commands(script)

    assert commands.count("set -eu") == 1
    assert commands[0] == "set -eu"

    migrations = [line for line in commands if "alembic upgrade head" in line]
    seeds = [line for line in commands if "app.scripts.seed_skill_ontology" in line]
    servers = [line for line in commands if "uvicorn" in line]
    exec_servers = [line for line in commands if line.startswith("exec ") and "uvicorn" in line]

    assert len(migrations) == 1
    assert len(seeds) == 1
    assert len(servers) == 1
    assert len(exec_servers) == 1
    assert exec_servers[0] == servers[0]

    migration_index = commands.index(migrations[0])
    seed_index = commands.index(seeds[0])
    server_index = commands.index(exec_servers[0])
    assert migration_index < seed_index < server_index

    joined = "\n".join(commands)
    assert "|| true" not in joined
    assert "sleep" not in joined
    assert "--reload" not in joined
