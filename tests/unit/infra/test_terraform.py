from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TF = ROOT / "infra" / "terraform"


class TestTerraformLayout:
    def test_required_files_exist(self) -> None:
        for name in (
            "versions.tf",
            "variables.tf",
            "main.tf",
            "outputs.tf",
            "prometheus.yml.tftpl",
        ):
            assert (TF / name).is_file(), name

    def test_docker_provider_and_monitoring_containers(self) -> None:
        versions = (TF / "versions.tf").read_text()
        main = (TF / "main.tf").read_text()
        assert "kreuzwerker/docker" in versions
        assert "docker_container" in main
        assert "ost-linker-prometheus-tf" in main
        assert "ost-linker-grafana-tf" in main
        assert "observability/prometheus/rules.yml" in main

    def test_template_uses_scrape_target(self) -> None:
        template = (TF / "prometheus.yml.tftpl").read_text()
        assert "${scrape_target}" in template
        assert "metrics_path: /metrics" in template
