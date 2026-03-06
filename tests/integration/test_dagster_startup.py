import subprocess
import time

import pytest

DAGSTER_BOOT_TIMEOUT = 60
DAGSTER_PORT = 3099


@pytest.mark.integration
class TestDagsterStartup:
    def test_dagster_dev_boots_without_errors(self) -> None:
        """Launch `dagster dev` and verify it starts without definition errors.

        This is the ultimate guard against asset key mismatches, broken
        imports, or any wiring issue that only surfaces at process startup
        (not caught by a simple Python import of `defs`).
        """
        proc = subprocess.Popen(
            [
                "uv",
                "run",
                "dagster",
                "dev",
                "-h",
                "127.0.0.1",
                "-p",
                str(DAGSTER_PORT),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        output_lines: list[str] = []
        webserver_ready = False
        definition_error = False
        error_detail = ""

        try:
            deadline = time.monotonic() + DAGSTER_BOOT_TIMEOUT
            while time.monotonic() < deadline:
                assert proc.stdout is not None
                line = proc.stdout.readline()
                if not line:
                    if proc.poll() is not None:
                        break
                    continue

                output_lines.append(line.rstrip())

                if "DagsterInvalidDefinitionError" in line:
                    definition_error = True
                    error_detail = line.strip()

                if "DagsterInvalidSubsetError" in line:
                    definition_error = True
                    error_detail = line.strip()

                if "Serving dagster-webserver on" in line:
                    webserver_ready = True
                    break

        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

        assert not definition_error, (
            f"Dagster failed to load definitions: {error_detail}"
        )
        assert webserver_ready, (
            "Dagster webserver did not start within "
            f"{DAGSTER_BOOT_TIMEOUT}s. Last output:\n" + "\n".join(output_lines[-10:])
        )
