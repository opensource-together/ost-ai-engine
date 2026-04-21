from pathlib import Path

import pytest

from src.linker.prompts.registry import (
    PromptNotFoundError,
    PromptValidationError,
    load_prompt,
)


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """Prevent cross-test contamination — registry memoizes by (name, version)."""
    load_prompt.cache_clear()


class TestLoadPrompt:
    def test_loads_classifier_v1(self) -> None:
        prompt = load_prompt("classifier", "v1")
        assert prompt.name == "classifier"
        assert prompt.version == "v1"
        assert "expert technical classifier" in prompt.system.lower()
        assert "{title}" not in prompt.system  # title is a user-side variable
        assert set(prompt.variables) == {"categories", "domains", "title", "context"}

    def test_missing_prompt_raises(self) -> None:
        with pytest.raises(PromptNotFoundError):
            load_prompt("classifier", "v999")


class TestFingerprint:
    def test_format(self) -> None:
        """Fingerprint has the form `<name>@<version>-<hash8>`."""
        prompt = load_prompt("classifier", "v1")
        assert prompt.fingerprint.startswith("classifier@v1-")
        suffix = prompt.fingerprint.split("-")[-1]
        assert len(suffix) == 8
        assert all(c in "0123456789abcdef" for c in suffix)

    def test_stable_across_loads(self) -> None:
        """Two loads of the same file must yield the same fingerprint."""
        load_prompt.cache_clear()
        first = load_prompt("classifier", "v1")
        load_prompt.cache_clear()
        second = load_prompt("classifier", "v1")
        assert first.fingerprint == second.fingerprint

    def test_content_change_changes_fingerprint(self, tmp_path: Path) -> None:
        """A silent edit to the YAML file must produce a new fingerprint."""
        from src.linker.prompts import registry

        original = registry._PROMPTS_DIR
        try:
            (tmp_path / "t").mkdir()
            base = (
                "name: t\nversion: v1\nsystem: 'hi {a}'\n"
                "user: '{b}'\nvariables: [a, b]\n"
            )
            (tmp_path / "t" / "v1.yaml").write_text(base)
            registry._PROMPTS_DIR = tmp_path
            load_prompt.cache_clear()
            fp1 = load_prompt("t", "v1").fingerprint

            (tmp_path / "t" / "v1.yaml").write_text(base + "# trailing change\n")
            load_prompt.cache_clear()
            fp2 = load_prompt("t", "v1").fingerprint

            assert fp1 != fp2
        finally:
            registry._PROMPTS_DIR = original
            load_prompt.cache_clear()


class TestRender:
    def test_renders_all_variables(self) -> None:
        prompt = load_prompt("classifier", "v1")
        system, user = prompt.render(
            categories="A, B",
            domains="X, Y",
            title="my project",
            context="some readme text",
        )
        assert "A, B" in system
        assert "X, Y" in system
        assert "my project" in user
        assert "some readme text" in user

    def test_missing_variable_raises(self) -> None:
        prompt = load_prompt("classifier", "v1")
        with pytest.raises(PromptValidationError, match="Missing variables"):
            prompt.render(categories="A", domains="X", title="t")

    def test_extra_variable_raises(self) -> None:
        prompt = load_prompt("classifier", "v1")
        with pytest.raises(PromptValidationError, match="Unexpected variables"):
            prompt.render(
                categories="A",
                domains="X",
                title="t",
                context="c",
                extra="nope",
            )

    def test_example_json_not_interpolated(self) -> None:
        """The `{{...}}` escape in the example JSON must render as literal `{...}`."""
        prompt = load_prompt("classifier", "v1")
        system, _ = prompt.render(categories="A", domains="X", title="t", context="c")
        assert '{"category": "Framework"' in system


class TestMetadataValidation:
    def test_mismatched_metadata_raises(self, tmp_path: Path) -> None:
        from src.linker.prompts import registry

        original = registry._PROMPTS_DIR
        try:
            (tmp_path / "bad").mkdir()
            (tmp_path / "bad" / "v1.yaml").write_text(
                "name: wrong\nversion: v1\nsystem: 's'\nuser: 'u'\nvariables: []\n"
            )
            registry._PROMPTS_DIR = tmp_path
            load_prompt.cache_clear()
            with pytest.raises(PromptValidationError, match="metadata mismatch"):
                load_prompt("bad", "v1")
        finally:
            registry._PROMPTS_DIR = original
            load_prompt.cache_clear()

    def test_declared_variables_must_match_template(self, tmp_path: Path) -> None:
        from src.linker.prompts import registry

        original = registry._PROMPTS_DIR
        try:
            (tmp_path / "drift").mkdir()
            (tmp_path / "drift" / "v1.yaml").write_text(
                "name: drift\nversion: v1\n"
                "system: 'hello {a}'\nuser: 'world'\nvariables: [a, b]\n"
            )
            registry._PROMPTS_DIR = tmp_path
            load_prompt.cache_clear()
            with pytest.raises(PromptValidationError, match="variables mismatch"):
                load_prompt("drift", "v1")
        finally:
            registry._PROMPTS_DIR = original
            load_prompt.cache_clear()
