"""Pure normalization of the bounded GitHub manifest subset (§17.6)."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from types import MappingProxyType
from typing import Mapping
import unicodedata
import xml.etree.ElementTree as element_tree

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.11 is required by the project
    tomllib = None  # type: ignore[assignment]


GITHUB_SNAPSHOT_SCHEMA_VERSION = 2
MAX_DISCOVERED_MANIFESTS = 50
MAX_MANIFEST_BYTES = 256 * 1024
MAX_DEPENDENCIES_PER_MANIFEST = 500
MAX_DEPENDENCIES_PER_REPOSITORY = 2_000
MAX_MANIFEST_WARNINGS = 200
MAX_DEPENDENCY_NAME_LENGTH = 255
MAX_NORMALIZED_PATH_LENGTH = 1_024

MANIFEST_KINDS = {
    "package.json": ("package_json", "npm"),
    "pyproject.toml": ("pyproject_toml", "python"),
    "requirements.txt": ("requirements_txt", "python"),
    "pom.xml": ("pom_xml", "maven"),
    "go.mod": ("go_mod", "go"),
    "Cargo.toml": ("cargo_toml", "cargo"),
    "composer.json": ("composer_json", "composer"),
    "Gemfile": ("gemfile", "rubygems"),
}
WARNING_CODES = frozenset(
    {
        "inaccessible",
        "oversized",
        "invalid_utf8",
        "malformed",
        "unsupported_syntax",
        "unsupported_dependency_source",
        "missing_required_field",
        "symlink_ignored",
        "submodule_ignored",
        "dependency_limit_exceeded",
        "manifest_limit_exceeded",
    }
)


class GitHubManifestValidationError(ValueError):
    """Base validation error for normalized manifest data."""


class InvalidManifestPathError(GitHubManifestValidationError):
    """A manifest path is not repository-relative and safe."""


class InvalidNormalizedDependencyError(GitHubManifestValidationError):
    """A normalized dependency violates the persisted DTO invariant."""


class ConflictingManifestIdentityError(GitHubManifestValidationError):
    """The same path was supplied with incompatible manifest kinds."""


@dataclass(frozen=True, slots=True)
class GitHubNormalizedDependency:
    name: str
    section: str | None
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_json_object(self.metadata))


@dataclass(frozen=True, slots=True)
class GitHubNormalizedManifest:
    path: str
    kind: str
    ecosystem: str
    dependencies: tuple[GitHubNormalizedDependency, ...]


@dataclass(frozen=True, slots=True)
class GitHubManifestWarning:
    path: str
    kind: str | None
    code: str
    detail: str | None


def normalize_manifest_path(path: str) -> str:
    if not isinstance(path, str):
        raise InvalidManifestPathError("manifest path must be a string")
    value = unicodedata.normalize("NFKC", path).replace("\\", "/")
    if (
        not value
        or len(value) > MAX_NORMALIZED_PATH_LENGTH
        or value.startswith("/")
        or "\x00" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise InvalidManifestPathError("manifest path is invalid")
    return value


def manifest_type(path: str) -> tuple[str, str] | None:
    name = path.rsplit("/", 1)[-1]
    if name in MANIFEST_KINDS:
        return MANIFEST_KINDS[name]
    if name.lower().endswith(".csproj"):
        return "csproj", "nuget"
    return None


def normalize_fixture_manifests(
    manifest_paths: tuple[str, ...], contents: Mapping[str, object]
) -> tuple[tuple[GitHubNormalizedManifest, ...], tuple[GitHubManifestWarning, ...]]:
    """Normalize fixture-only raw contents without exposing them in the DTO."""
    normalized = sorted({normalize_manifest_path(path) for path in manifest_paths})
    discovered: list[tuple[str, tuple[str, str] | None]] = [
        (path, manifest_type(path)) for path in normalized
    ]
    known_manifests: list[tuple[str, tuple[str, str]]] = []
    for path, kind in discovered:
        if kind is not None:
            known_manifests.append((path, kind))
    warnings: list[GitHubManifestWarning] = []
    if len(known_manifests) > MAX_DISCOVERED_MANIFESTS:
        overflow = known_manifests[MAX_DISCOVERED_MANIFESTS:]
        first_overflow_path, first_overflow_kind = overflow[0]
        warnings.append(
            _warning(first_overflow_path, first_overflow_kind[0], "manifest_limit_exceeded")
        )
        known_manifests = known_manifests[:MAX_DISCOVERED_MANIFESTS]

    manifests: list[GitHubNormalizedManifest] = []
    total_dependencies = 0
    for path, (manifest_kind, ecosystem) in known_manifests:
        raw_content = contents.get(path)
        if raw_content is None:
            warnings.append(_warning(path, manifest_kind, "inaccessible"))
            continue
        if not isinstance(raw_content, (str, bytes)):
            warnings.append(_warning(path, manifest_kind, "inaccessible"))
            continue
        raw_bytes = raw_content.encode("utf-8") if isinstance(raw_content, str) else raw_content
        if len(raw_bytes) > MAX_MANIFEST_BYTES:
            warnings.append(_warning(path, manifest_kind, "oversized"))
            continue
        try:
            content = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            warnings.append(_warning(path, manifest_kind, "invalid_utf8"))
            continue
        dependencies, parser_warnings = parse_manifest(path, content)
        available = MAX_DEPENDENCIES_PER_REPOSITORY - total_dependencies
        if len(dependencies) > available:
            dependencies = dependencies[: max(available, 0)]
            parser_warnings = (
                *parser_warnings,
                _warning(path, manifest_kind, "dependency_limit_exceeded"),
            )
        total_dependencies += len(dependencies)
        manifests.append(GitHubNormalizedManifest(path, manifest_kind, ecosystem, dependencies))
        warnings.extend(parser_warnings)
    return (
        tuple(sorted(manifests, key=lambda value: (value.path, value.kind))),
        tuple(sorted(_unique_warnings(warnings), key=_warning_key)[:MAX_MANIFEST_WARNINGS]),
    )


def parse_manifest(
    path: str, content: str
) -> tuple[tuple[GitHubNormalizedDependency, ...], tuple[GitHubManifestWarning, ...]]:
    kind_info = manifest_type(path)
    if kind_info is None:
        return (), ()
    kind = kind_info[0]
    try:
        if kind == "package_json":
            dependencies, warnings = _json_dependencies(
                path,
                content,
                ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"),
                False,
            )
        elif kind == "composer_json":
            dependencies, warnings = _json_dependencies(
                path, content, ("require", "require-dev"), True
            )
        elif kind == "pyproject_toml":
            dependencies, warnings = _pyproject(path, content)
        elif kind == "requirements_txt":
            dependencies, warnings = _requirements(path, content)
        elif kind == "pom_xml":
            dependencies, warnings = _pom(path, content)
        elif kind == "go_mod":
            dependencies, warnings = _go_mod(path, content)
        elif kind == "cargo_toml":
            dependencies, warnings = _cargo(path, content)
        elif kind == "gemfile":
            dependencies, warnings = _gemfile(path, content)
        else:
            dependencies, warnings = _csproj(path, content)
    except InvalidNormalizedDependencyError:
        raise
    except (json.JSONDecodeError, element_tree.ParseError, ValueError, TypeError):
        return (), (_warning(path, kind, "malformed"),)
    return _limit_dependencies(path, kind, dependencies, warnings)


def _json_dependencies(
    path: str, content: str, sections: tuple[str, ...], composer: bool
) -> tuple[list[GitHubNormalizedDependency], list[GitHubManifestWarning]]:
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError
    records: list[GitHubNormalizedDependency] = []
    for section in sections:
        values = data.get(section, {})
        if not isinstance(values, dict):
            raise ValueError
        for raw_name in values:
            if not isinstance(raw_name, str):
                raise ValueError
            name = _simple_name(raw_name)
            if composer and (
                name == "php"
                or name.startswith(("ext-", "lib-"))
                or name in {"composer-plugin-api", "composer-runtime-api"}
            ):
                continue
            records.append(_dependency(name, section, {}))
    return records, []


def _pyproject(
    path: str, content: str
) -> tuple[list[GitHubNormalizedDependency], list[GitHubManifestWarning]]:
    if tomllib is None:
        raise ValueError
    data = tomllib.loads(content)
    records: list[GitHubNormalizedDependency] = []
    warnings: list[GitHubManifestWarning] = []
    project = data.get("project", {})
    if isinstance(project, dict):
        records.extend(
            _python_items(
                project.get("dependencies", []), "project.dependencies", None, path, warnings
            )
        )
        optional = project.get("optional-dependencies", {})
        if isinstance(optional, dict):
            for group, values in optional.items():
                if isinstance(group, str):
                    records.extend(
                        _python_items(
                            values, f"project.optional-dependencies.{group}", group, path, warnings
                        )
                    )
    tool = data.get("tool", {})
    poetry = tool.get("poetry", {}) if isinstance(tool, dict) else {}
    if isinstance(poetry, dict):
        dependencies = poetry.get("dependencies", {})
        if isinstance(dependencies, dict):
            for name, declaration in dependencies.items():
                if name != "python":
                    records.extend(
                        _poetry_item(
                            name, declaration, "tool.poetry.dependencies", None, path, warnings
                        )
                    )
        groups = poetry.get("group", {})
        if isinstance(groups, dict):
            for group, group_data in groups.items():
                deps = group_data.get("dependencies", {}) if isinstance(group_data, dict) else {}
                if isinstance(group, str) and isinstance(deps, dict):
                    for name, declaration in deps.items():
                        records.extend(
                            _poetry_item(
                                name,
                                declaration,
                                f"tool.poetry.group.{group}.dependencies",
                                group,
                                path,
                                warnings,
                            )
                        )
    return records, warnings


def _poetry_item(
    name: object,
    declaration: object,
    section: str,
    group: str | None,
    path: str,
    warnings: list[GitHubManifestWarning],
) -> list[GitHubNormalizedDependency]:
    if not isinstance(name, str):
        warnings.append(_warning(path, "pyproject_toml", "unsupported_syntax"))
        return []
    if isinstance(declaration, str) and ("://" in declaration or "git+" in declaration):
        warnings.append(_warning(path, "pyproject_toml", "unsupported_dependency_source"))
        return []
    if isinstance(declaration, dict) and ("git" in declaration or "path" in declaration):
        warnings.append(_warning(path, "pyproject_toml", "unsupported_dependency_source"))
        return []
    return _python_items([name], section, group, path, warnings)


def _python_items(
    values: object,
    section: str,
    group: str | None,
    path: str,
    warnings: list[GitHubManifestWarning],
) -> list[GitHubNormalizedDependency]:
    if not isinstance(values, list):
        return []
    result: list[GitHubNormalizedDependency] = []
    for value in values:
        if not isinstance(value, str):
            warnings.append(_warning(path, "pyproject_toml", "unsupported_syntax"))
            continue
        if "@" in value or re.search(r"(?:git\+|://|(?:^|\s)(?:\.|/))", value):
            warnings.append(_warning(path, "pyproject_toml", "unsupported_dependency_source"))
            continue
        name = _python_name(value)
        result.append(_dependency(name, section, {"group": group}))
    return result


def _requirements(
    path: str, content: str
) -> tuple[list[GitHubNormalizedDependency], list[GitHubManifestWarning]]:
    records: list[GitHubNormalizedDependency] = []
    warnings: list[GitHubManifestWarning] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if (
            line.startswith(
                (
                    "-r",
                    "--requirement",
                    "-c",
                    "--constraint",
                    "-e",
                    "--editable",
                    "--index",
                    "--trusted-host",
                    "--hash",
                )
            )
            or "://" in line
            or line.startswith(("git+", ".", "/"))
        ):
            warnings.append(_warning(path, "requirements_txt", "unsupported_dependency_source"))
            continue
        name = _python_name(line)
        records.append(_dependency(name, None, {}))
    return records, warnings


def _pom(
    path: str, content: str
) -> tuple[list[GitHubNormalizedDependency], list[GitHubManifestWarning]]:
    _reject_xml_entities(content)
    root = element_tree.fromstring(content)
    records: list[GitHubNormalizedDependency] = []
    warnings: list[GitHubManifestWarning] = []
    parents = {child: parent for parent in root.iter() for child in parent}
    for parent in root.iter():
        if _local(parent.tag) != "dependencies" or _has_dependency_management_parent(
            parent, parents
        ):
            continue
        for dependency in parent:
            if _local(dependency.tag) != "dependency":
                continue
            values = {_local(child.tag): (child.text or "").strip() for child in dependency}
            group, artifact = values.get("groupId"), values.get("artifactId")
            if not group or not artifact or "${" in group or "${" in artifact:
                warnings.append(_warning(path, "pom_xml", "missing_required_field"))
                continue
            name = _simple_name(group) + ":" + _simple_name(artifact)
            records.append(
                _dependency(
                    name,
                    "dependencies",
                    {"group_id": group.lower(), "artifact_id": artifact.lower()},
                )
            )
    return records, warnings


def _go_mod(
    path: str, content: str
) -> tuple[list[GitHubNormalizedDependency], list[GitHubManifestWarning]]:
    records: list[GitHubNormalizedDependency] = []
    in_block = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "require (":
            in_block = True
            continue
        if in_block and stripped == ")":
            in_block = False
            continue
        candidate = (
            stripped
            if in_block
            else (stripped[8:].strip() if stripped.startswith("require ") else "")
        )
        if not candidate:
            continue
        parts = candidate.split()
        if len(parts) >= 2:
            records.append(
                _dependency(parts[0], "require", {"indirect": "// indirect" in candidate})
            )
    return records, []


def _cargo(
    path: str, content: str
) -> tuple[list[GitHubNormalizedDependency], list[GitHubManifestWarning]]:
    if tomllib is None:
        raise ValueError
    data = tomllib.loads(content)
    records: list[GitHubNormalizedDependency] = []
    warnings: list[GitHubManifestWarning] = []
    for section, target in _cargo_sections(data):
        values = _get_dotted(data, section)
        if not isinstance(values, dict):
            continue
        for alias, value in values.items():
            if not isinstance(alias, str):
                continue
            package = value.get("package") if isinstance(value, dict) else alias
            if not isinstance(package, str) or (
                isinstance(value, dict)
                and "package" not in value
                and ("git" in value or "path" in value)
            ):
                warnings.append(_warning(path, "cargo_toml", "unsupported_dependency_source"))
                continue
            records.append(
                _dependency(
                    package,
                    section,
                    {"alias": alias if package != alias else None, "target": target},
                )
            )
    return records, warnings


def _cargo_sections(data: Mapping[str, object]) -> list[tuple[str, str | None]]:
    base: list[tuple[str, str | None]] = [
        (name, None) for name in ("dependencies", "dev-dependencies", "build-dependencies")
    ]
    target = data.get("target")
    if isinstance(target, dict):
        for selector, table in target.items():
            if isinstance(selector, str) and isinstance(table, dict):
                base.extend(
                    (f"target.{selector}.{name}", selector)
                    for name in ("dependencies", "dev-dependencies", "build-dependencies")
                )
    return base


def _gemfile(
    path: str, content: str
) -> tuple[list[GitHubNormalizedDependency], list[GitHubManifestWarning]]:
    records: list[GitHubNormalizedDependency] = []
    warnings: list[GitHubManifestWarning] = []
    for line in content.splitlines():
        match = re.match(r"^\s*gem\s+(['\"])([^'\"]+)\1", line)
        if match:
            records.append(_dependency(match.group(2), "gem", {}))
        elif line.strip().startswith("gem "):
            warnings.append(_warning(path, "gemfile", "unsupported_syntax"))
    return records, warnings


def _csproj(
    path: str, content: str
) -> tuple[list[GitHubNormalizedDependency], list[GitHubManifestWarning]]:
    _reject_xml_entities(content)
    root = element_tree.fromstring(content)
    records: list[GitHubNormalizedDependency] = []
    warnings: list[GitHubManifestWarning] = []
    for element in root.iter():
        if _local(element.tag) != "PackageReference":
            continue
        name = element.attrib.get("Include") or element.attrib.get("Update")
        if not name:
            warnings.append(_warning(path, "csproj", "missing_required_field"))
            continue
        records.append(_dependency(name, "PackageReference", {}))
    return records, warnings


def _limit_dependencies(
    path: str,
    kind: str,
    records: list[GitHubNormalizedDependency],
    warnings: list[GitHubManifestWarning],
) -> tuple[tuple[GitHubNormalizedDependency, ...], tuple[GitHubManifestWarning, ...]]:
    ordered = sorted(_unique_dependencies(records), key=_dependency_key)
    if len(ordered) > MAX_DEPENDENCIES_PER_MANIFEST:
        ordered = ordered[:MAX_DEPENDENCIES_PER_MANIFEST]
        warnings.append(_warning(path, kind, "dependency_limit_exceeded"))
    return tuple(ordered), tuple(sorted(_unique_warnings(warnings), key=_warning_key))


def _dependency(
    name: str, section: str | None, metadata: Mapping[str, object]
) -> GitHubNormalizedDependency:
    normalized = unicodedata.normalize("NFKC", name).strip().lower()
    if not normalized or len(normalized) > MAX_DEPENDENCY_NAME_LENGTH:
        raise InvalidNormalizedDependencyError("dependency name is invalid")
    return GitHubNormalizedDependency(normalized, section, metadata)


def _simple_name(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().lower()


def _python_name(value: str) -> str:
    name = value.split(";", 1)[0].split("[", 1)[0]
    name = re.split(r"\s*(?:===|==|!=|<=|>=|~=|<|>|@)\s*", name, maxsplit=1)[0]
    return re.sub(r"[-_.]+", "-", _simple_name(name))


def _warning(
    path: str, kind: str | None, code: str, detail: str | None = None
) -> GitHubManifestWarning:
    if code not in WARNING_CODES:
        raise GitHubManifestValidationError("warning code is invalid")
    return GitHubManifestWarning(path, kind, code, detail)


def _reject_xml_entities(content: str) -> None:
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)", content, re.IGNORECASE):
        raise ValueError


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _has_dependency_management_parent(
    element: element_tree.Element, parents: Mapping[element_tree.Element, element_tree.Element]
) -> bool:
    current = parents.get(element)
    while current is not None:
        if _local(current.tag) == "dependencyManagement":
            return True
        current = parents.get(current)
    return False


def _get_dotted(value: Mapping[str, object], path: str) -> object:
    result: object = value
    for part in path.split("."):
        if not isinstance(result, dict):
            return None
        result = result.get(part)
    return result


def _dependency_key(value: GitHubNormalizedDependency) -> tuple[str, str, str]:
    return (
        value.name,
        value.section or "",
        json.dumps(
            _thaw_json_value(value.metadata),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    )


def _warning_key(value: GitHubManifestWarning) -> tuple[str, str, str]:
    return value.path, value.code, value.detail or ""


def _unique_dependencies(
    values: list[GitHubNormalizedDependency],
) -> list[GitHubNormalizedDependency]:
    unique: dict[tuple[str, str, str], GitHubNormalizedDependency] = {}
    for value in values:
        unique[_dependency_key(value)] = value
    return list(unique.values())


def _unique_warnings(values: list[GitHubManifestWarning]) -> list[GitHubManifestWarning]:
    unique: dict[tuple[str, str | None, str, str | None], GitHubManifestWarning] = {}
    for value in values:
        unique[(value.path, value.kind, value.code, value.detail)] = value
    return list(unique.values())


def _freeze_json_object(value: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise GitHubManifestValidationError("dependency metadata must be a JSON object")
    return MappingProxyType({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return tuple(_freeze_json_value(item) for item in value)
    raise GitHubManifestValidationError("dependency metadata is not JSON-compatible")


def thaw_json_value(value: object) -> object:
    """Return a detached JSON-compatible representation of immutable DTO metadata."""
    return _thaw_json_value(value)


def _thaw_json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json_value(item) for item in value]
    return value
