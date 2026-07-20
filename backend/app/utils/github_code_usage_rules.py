"""Static, bounded rules for deterministic GitHub source-usage extraction."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final, Pattern


EXCLUDED_PATH_PARTS: Final = frozenset({"node_modules", "vendor", "dist", "build", "coverage", ".next", "target", "generated"})
LOCKFILE_NAMES: Final = frozenset({"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "pipfile.lock"})
SOURCE_EXTENSIONS: Final = frozenset({".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".css", ".json", ".yml", ".yaml"})
CONFIG_FILENAMES: Final = frozenset({"vite.config.js", "vite.config.ts", "next.config.js", "next.config.mjs", "next.config.ts", "tailwind.config.js", "tailwind.config.ts", "tsconfig.json", "pytest.ini", "alembic.ini", "dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml", ".dockerignore"})


@dataclass(frozen=True, slots=True)
class GitHubCodeUsageRule:
    target_skill_name: str
    extensions: frozenset[str]
    imports: tuple[Pattern[str], ...] = ()
    api_calls: tuple[Pattern[str], ...] = ()
    class_or_function_usage: tuple[Pattern[str], ...] = ()
    config_files: tuple[Pattern[str], ...] = ()
    config_patterns: tuple[Pattern[str], ...] = ()
    ci_patterns: tuple[Pattern[str], ...] = ()


def is_excluded_analysis_path(path: str) -> bool:
    lower_path = path.lower()
    name = lower_path.rsplit("/", 1)[-1]
    return any(part in EXCLUDED_PATH_PARTS for part in lower_path.split("/")) or name in LOCKFILE_NAMES or name.endswith(".min.js") or "/migrations/versions/" in f"/{lower_path}"


def is_analyzable_source_path(path: str) -> bool:
    if is_excluded_analysis_path(path):
        return False
    name = path.lower().rsplit("/", 1)[-1]
    return name in CONFIG_FILENAMES or any(name.endswith(extension) for extension in SOURCE_EXTENSIONS)


def is_test_path(path: str) -> bool:
    name = path.lower().rsplit("/", 1)[-1]
    return "/tests/" in f"/{path.lower()}" or "/__tests__/" in f"/{path.lower()}" or name.startswith("test_") or name.endswith("_test.py") or name.endswith((".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx"))


def _patterns(*values: str) -> tuple[Pattern[str], ...]:
    return tuple(re.compile(value, re.MULTILINE) for value in values)


_JS = frozenset({".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"})
_PY = frozenset({".py"})

GITHUB_CODE_USAGE_RULES: Final[tuple[GitHubCodeUsageRule, ...]] = (
    GitHubCodeUsageRule("React", _JS, imports=_patterns(r"\bimport(?:\s+.+?\s+from)?\s*[\"']react[\"']", r"\brequire\([\"']react[\"']\)"), api_calls=_patterns(r"\b(?:useState|useEffect|useMemo|useCallback|createContext)\s*\(", r"\bReactDOM\.createRoot\s*\(")),
    GitHubCodeUsageRule("TypeScript", frozenset({".ts", ".tsx"}), config_files=_patterns(r"(?:^|/)tsconfig\.json$")),
    GitHubCodeUsageRule("JavaScript", frozenset({".js", ".jsx", ".mjs", ".cjs"})),
    GitHubCodeUsageRule("Node.js", _JS, imports=_patterns(r"\bfrom\s+[\"']node:", r"\brequire\([\"'](?:node:)?(?:fs|path|http|process)[\"']\)")),
    GitHubCodeUsageRule("Express", _JS, imports=_patterns(r"\bimport(?:\s+.+?\s+from)?\s*[\"']express[\"']", r"\brequire\([\"']express[\"']\)"), api_calls=_patterns(r"\bexpress\s*\(", r"\b(?:Router|app\.(?:get|post|use)|router\.(?:get|post))\s*\(")),
    GitHubCodeUsageRule("Python", _PY),
    GitHubCodeUsageRule("FastAPI", _PY, imports=_patterns(r"\bfrom\s+fastapi(?:\.|\s+import)", r"\bimport\s+fastapi\b"), api_calls=_patterns(r"\b(?:FastAPI|APIRouter|Depends|HTTPException)\s*\(", r"@(?:router|app)\.(?:get|post)\s*\(")),
    GitHubCodeUsageRule("Pytest", _PY, imports=_patterns(r"\bimport\s+pytest\b", r"\bfrom\s+pytest\s+import"), api_calls=_patterns(r"@pytest\.(?:fixture|mark)\b", r"\bpytest\.raises\s*\("), config_files=_patterns(r"(?:^|/)(?:pytest\.ini|pyproject\.toml)$"), config_patterns=_patterns(r"\[tool\.pytest", r"\[pytest\]"), ci_patterns=_patterns(r"\bpytest\b")),
    GitHubCodeUsageRule("PostgreSQL", _PY | _JS, imports=_patterns(r"\bimport\s+psycopg\b", r"\bfrom\s+psycopg", r"\bfrom\s+asyncpg", r"\bfrom\s+[\"']pg[\"']"), class_or_function_usage=_patterns(r"\b(?:psycopg|asyncpg|create_engine)\b"), config_patterns=_patterns(r"(?:postgresql|postgres)://"), ci_patterns=_patterns(r"\b(?:postgres|postgresql)\b")),
    GitHubCodeUsageRule("SQLAlchemy", _PY, imports=_patterns(r"\bfrom\s+sqlalchemy", r"\bimport\s+sqlalchemy"), class_or_function_usage=_patterns(r"\b(?:Session|declarative_base|Mapped|relationship|create_engine)\b"), config_files=_patterns(r"(?:^|/)alembic\.ini$"), config_patterns=_patterns(r"\bsqlalchemy\.url\b"), ci_patterns=_patterns(r"\balembic\s+(?:upgrade|downgrade)\b")),
    GitHubCodeUsageRule("Redis", _PY | _JS, imports=_patterns(r"\bimport\s+redis\b", r"\bfrom\s+redis", r"\bfrom\s+[\"']redis[\"']"), class_or_function_usage=_patterns(r"\b(?:Redis|StrictRedis|createClient)\s*\("), config_patterns=_patterns(r"redis://"), ci_patterns=_patterns(r"\bredis\b")),
    GitHubCodeUsageRule("MongoDB", _PY | _JS, imports=_patterns(r"\bfrom\s+pymongo", r"\bimport\s+pymongo", r"\bfrom\s+[\"']mongoose[\"']"), class_or_function_usage=_patterns(r"\b(?:MongoClient|mongoose\.model)\b"), config_patterns=_patterns(r"mongodb(?:\+srv)?://")),
    GitHubCodeUsageRule("Next.js", _JS, imports=_patterns(r"\bfrom\s+[\"']next(?:/|[\"'])"), class_or_function_usage=_patterns(r"\b(?:getServerSideProps|getStaticProps|NextResponse)\b"), config_files=_patterns(r"(?:^|/)next\.config\.(?:js|mjs|ts)$")),
    GitHubCodeUsageRule("Tailwind CSS", _JS | frozenset({".css"}), config_files=_patterns(r"(?:^|/)tailwind\.config\.(?:js|ts)$"), config_patterns=_patterns(r"@tailwind\s+(?:base|components|utilities)")),
)
