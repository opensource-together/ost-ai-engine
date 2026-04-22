"""Prompt registry — load versioned LLM prompts from YAML and fingerprint them.

Prompts live under `src/linker/prompts/<name>/<version>.yaml`. Each file declares
its own metadata (name, version, description, variables, system, user). The
registry loads them, validates that declared variables match template
placeholders, and produces a stable fingerprint of the form
`<name>@<version>-<sha8>` so the pipeline can attribute every classification to
the exact prompt text that produced it.

Why a fingerprint in addition to the version string: renaming a file to v2 is
a deliberate act, but a silent edit inside v1.yaml would otherwise be invisible
in the audit trail. The content hash makes such edits detectable.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

_PROMPTS_DIR = Path(__file__).parent
_PLACEHOLDER_RE = re.compile(r"(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)\}(?!\})")


class PromptNotFoundError(FileNotFoundError):
    """Raised when a prompt file cannot be located on disk."""


class PromptValidationError(ValueError):
    """Raised when a prompt YAML is malformed or inconsistent."""


@dataclass(frozen=True)
class PromptTemplate:
    """Immutable, rendered-on-demand prompt template.

    The `fingerprint` uniquely identifies both the declared version AND the
    actual content; two loads of the same file always return the same value.
    """

    name: str
    version: str
    description: str
    variables: tuple[str, ...]
    system: str
    user: str
    fingerprint: str

    def render(self, **kwargs: str) -> tuple[str, str]:
        """Render both system and user messages, validating variables."""
        missing = set(self.variables) - set(kwargs)
        if missing:
            raise PromptValidationError(
                f"Missing variables for prompt {self.name}@{self.version}: "
                f"{sorted(missing)}"
            )
        extra = set(kwargs) - set(self.variables)
        if extra:
            raise PromptValidationError(
                f"Unexpected variables for prompt {self.name}@{self.version}: "
                f"{sorted(extra)}"
            )
        return self.system.format(**kwargs), self.user.format(**kwargs)


def _extract_placeholders(text: str) -> set[str]:
    """Extract `{var}` placeholders, ignoring escaped `{{` / `}}`."""
    return set(_PLACEHOLDER_RE.findall(text))


def _fingerprint(content: bytes, name: str, version: str) -> str:
    digest = hashlib.sha256(content).hexdigest()[:8]
    return f"{name}@{version}-{digest}"


@lru_cache(maxsize=32)
def load_prompt(name: str, version: str) -> PromptTemplate:
    """Load and validate a prompt from `<name>/<version>.yaml`.

    Results are memoized per (name, version) — the registry is effectively
    read-only at runtime. Call `load_prompt.cache_clear()` in tests that mutate
    prompt files on disk.
    """
    path = _PROMPTS_DIR / name / f"{version}.yaml"
    if not path.is_file():
        raise PromptNotFoundError(f"Prompt not found: {path}")

    raw = path.read_bytes()
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise PromptValidationError(f"Invalid YAML at {path}: {e}") from e

    if not isinstance(data, dict):
        raise PromptValidationError(f"Prompt {path} must be a mapping")

    for required in ("name", "version", "system", "user", "variables"):
        if required not in data:
            raise PromptValidationError(f"Prompt {path} missing key: {required}")

    if data["name"] != name or data["version"] != version:
        raise PromptValidationError(
            f"Prompt {path} metadata mismatch: "
            f"declared {data['name']}@{data['version']}, expected {name}@{version}"
        )

    declared = set(data["variables"] or [])
    found = _extract_placeholders(data["system"]) | _extract_placeholders(data["user"])
    if declared != found:
        raise PromptValidationError(
            f"Prompt {path} variables mismatch: "
            f"declared={sorted(declared)}, in_template={sorted(found)}"
        )

    return PromptTemplate(
        name=name,
        version=version,
        description=data.get("description", ""),
        variables=tuple(sorted(declared)),
        system=data["system"],
        user=data["user"],
        fingerprint=_fingerprint(raw, name, version),
    )
