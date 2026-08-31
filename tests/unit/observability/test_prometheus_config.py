from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
PROM = ROOT / "observability" / "prometheus"
GRAFANA = ROOT / "observability" / "grafana"


class TestPrometheusConfig:
    def test_scrapes_linker_api_metrics(self) -> None:
        config = yaml.safe_load((PROM / "prometheus.yml").read_text())
        jobs = {job["job_name"]: job for job in config["scrape_configs"]}
        api = jobs["linker-api"]
        assert api["metrics_path"] == "/metrics"
        assert api["static_configs"][0]["targets"] == ["api:8000"]
        assert "/etc/prometheus/rules.yml" in config["rule_files"]

    def test_alert_rules_cover_down_and_error_rate(self) -> None:
        rules = yaml.safe_load((PROM / "rules.yml").read_text())
        names = {rule["alert"] for rule in rules["groups"][0]["rules"]}
        assert names == {"LinkerApiDown", "LinkerApiHighErrorRate"}


class TestGrafanaProvisioning:
    def test_datasource_points_at_prometheus(self) -> None:
        data = yaml.safe_load(
            (GRAFANA / "provisioning" / "datasources" / "prometheus.yml").read_text()
        )
        source = data["datasources"][0]
        assert source["url"] == "http://prometheus:9090"
        assert source["uid"] == "prometheus"

    def test_dashboard_uid_is_stable(self) -> None:
        import json

        dashboard = json.loads((GRAFANA / "dashboards" / "linker-api.json").read_text())
        assert dashboard["uid"] == "ost-linker-api"
        assert dashboard["title"] == "OST Linker API"
