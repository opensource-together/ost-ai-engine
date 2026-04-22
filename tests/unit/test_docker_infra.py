from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestDockerfile:
    def test_dockerfile_exists(self) -> None:
        assert (PROJECT_ROOT / "Dockerfile").is_file()

    def test_non_root_user(self) -> None:
        """Dockerfile must switch to a non-root user before CMD."""
        content = (PROJECT_ROOT / "Dockerfile").read_text()
        lines = content.splitlines()
        user_line_idx = None
        cmd_line_idx = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("USER ") and not stripped.startswith("USER root"):
                user_line_idx = i
            if stripped.startswith("CMD "):
                cmd_line_idx = i
        assert user_line_idx is not None, "Dockerfile must contain a non-root USER"
        assert cmd_line_idx is not None, "Dockerfile must contain a CMD"
        assert user_line_idx < cmd_line_idx, "USER must come before CMD"

    def test_healthcheck_defined(self) -> None:
        content = (PROJECT_ROOT / "Dockerfile").read_text()
        assert "HEALTHCHECK" in content

    def test_go_binaries_copied(self) -> None:
        content = (PROJECT_ROOT / "Dockerfile").read_text()
        assert "ost-scraper" in content
        assert "ost-fetcher" in content

    def test_hf_cache_dirs_configured(self) -> None:
        """SentenceTransformer (used by embedding assets) needs writable cache
        dirs. The non-root `appuser` has no home dir, so the default
        ~/.cache/huggingface fails with PermissionError. Pin HF_HOME and
        SENTENCE_TRANSFORMERS_HOME to a writable /app path."""
        content = (PROJECT_ROOT / "Dockerfile").read_text()
        assert "HF_HOME=/app/" in content, "HF_HOME must be set to a writable /app path"
        assert "SENTENCE_TRANSFORMERS_HOME=/app/" in content, (
            "SENTENCE_TRANSFORMERS_HOME must be set to a writable /app path"
        )
        assert "chown" in content and "/app/.cache" in content, (
            "HF cache dir must be chown'd to appuser"
        )

    def test_no_hardcoded_secrets(self) -> None:
        """Dockerfile must not contain hardcoded passwords or tokens."""
        content = (PROJECT_ROOT / "Dockerfile").read_text().lower()
        for keyword in ("password=", "api_key=", "secret=", "token="):
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                assert keyword not in stripped, (
                    f"Possible hardcoded secret ({keyword}) in Dockerfile"
                )


class TestDockerCompose:
    def test_compose_file_is_valid_yaml(self) -> None:
        with open(PROJECT_ROOT / "docker-compose.yml") as f:
            config = yaml.safe_load(f)
        assert "services" in config

    def test_override_file_is_valid_yaml(self) -> None:
        override = PROJECT_ROOT / "docker-compose.override.yml"
        if not override.exists():
            return
        with open(override) as f:
            config = yaml.safe_load(f)
        assert "services" in config

    def test_webserver_service_exists(self) -> None:
        with open(PROJECT_ROOT / "docker-compose.yml") as f:
            config = yaml.safe_load(f)
        assert "webserver" in config["services"]

    def test_webserver_has_healthcheck(self) -> None:
        with open(PROJECT_ROOT / "docker-compose.yml") as f:
            config = yaml.safe_load(f)
        webserver = config["services"]["webserver"]
        assert "healthcheck" in webserver
        assert "test" in webserver["healthcheck"]

    def test_webserver_exposes_port_3000(self) -> None:
        with open(PROJECT_ROOT / "docker-compose.yml") as f:
            config = yaml.safe_load(f)
        ports = config["services"]["webserver"].get("ports", [])
        port_strs = [str(p) for p in ports]
        assert any("3000" in p for p in port_strs)

    def test_daemon_depends_on_webserver(self) -> None:
        with open(PROJECT_ROOT / "docker-compose.yml") as f:
            config = yaml.safe_load(f)
        daemon = config["services"]["daemon"]
        depends = daemon.get("depends_on", {})
        assert "webserver" in depends

    def test_no_hardcoded_secrets_in_compose(self) -> None:
        """Compose env values must use ${VAR} substitution, not literals."""
        with open(PROJECT_ROOT / "docker-compose.yml") as f:
            config = yaml.safe_load(f)
        env_anchor = config.get("x-common-env", {})
        if not env_anchor:
            return
        secret_keys = {"DATABASE_URL", "GITHUB_ACCESS_TOKEN", "MISTRAL_API_KEY"}
        for key in secret_keys:
            if key in env_anchor:
                val = str(env_anchor[key])
                assert val.startswith("${") or val == "", (
                    f"{key} appears hardcoded in docker-compose.yml"
                )

    def test_dev_db_uses_env_for_credentials(self) -> None:
        """Dev override DB must not hardcode credentials."""
        override = PROJECT_ROOT / "docker-compose.override.yml"
        if not override.exists():
            return
        with open(override) as f:
            config = yaml.safe_load(f)
        db = config.get("services", {}).get("db", {})
        env = db.get("environment", {})
        for key in ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"):
            if key in env:
                val = str(env[key])
                assert val.startswith("${"), (
                    f"{key} appears hardcoded in docker-compose.override.yml"
                )
