"""Consistency checks across the Lab 6 config files (standard library only).

These parse and cross-reference text; they do not start Prometheus, Grafana or
Jenkins. `promtool check config`, Compose and the pipeline itself are the real
validation and need Docker.
"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).parent


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def exposed_metric_names():
    """Metric names the exporter exposes, derived from delivery_metrics.py."""
    src = read("exporter/delivery_metrics.py")
    names = set()
    for kind, name in re.findall(r'(Counter|Gauge|Summary)\(\s*"([a-z_]+)"', src):
        if kind == "Counter":
            names.add(f"{name}_total")
        elif kind == "Summary":
            names.update({f"{name}_sum", f"{name}_count"})
        else:
            names.add(name)
    return names


def referenced_metric_names(expr):
    # Drop quoted label values such as job="delivery_service" first.
    expr = re.sub(r'"[^"]*"', "", expr)
    return set(re.findall(r"\b(deliver[a-z_]+)\b", expr))


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dash = json.loads(read("grafana/provisioning/dashboards/delivery.json"))

    def test_has_four_panels_with_unique_ids(self):
        ids = [p["id"] for p in self.dash["panels"]]
        self.assertEqual(len(ids), 4)
        self.assertEqual(len(set(ids)), 4)

    def test_panels_use_provisioned_datasource_uid(self):
        for panel in self.dash["panels"]:
            self.assertEqual(panel["datasource"]["uid"], "prometheus")
        self.assertIn("uid: prometheus", read("grafana/provisioning/datasources/prometheus.yml"))

    def test_queries_only_reference_exposed_metrics(self):
        exposed = exposed_metric_names()
        for panel in self.dash["panels"]:
            for target in panel["targets"]:
                self.assertTrue(
                    referenced_metric_names(target["expr"]) <= exposed,
                    f"unknown metric in {target['expr']!r}",
                )


class PrometheusTests(unittest.TestCase):
    def test_scrapes_exporter_by_service_name(self):
        text = read("prometheus/prometheus.yml")
        self.assertIn("exporter:8000", text)
        self.assertNotIn("172.17.0.1", text)

    def test_rule_file_is_referenced_and_copied(self):
        self.assertIn("/etc/prometheus/alert_rules.yml", read("prometheus/prometheus.yml"))
        self.assertIn("alert_rules.yml", read("prometheus/Dockerfile"))

    def test_alert_rules(self):
        text = read("prometheus/alert_rules.yml")
        for name in ("HighPendingDeliveries", "HighAverageDeliveryTime", "DeliveryServiceDown"):
            self.assertIn(f"alert: {name}", text)
        self.assertIn("rate(delivery_duration_seconds_sum[1m])", text)

    def test_alert_expressions_reference_exposed_metrics(self):
        exposed = exposed_metric_names()
        for expr in re.findall(r"expr: (.+)", read("prometheus/alert_rules.yml")):
            names = referenced_metric_names(expr)
            self.assertTrue(names <= exposed, f"unknown metric in {expr!r}")

    def test_yaml_has_no_tabs(self):
        for rel in ("prometheus/prometheus.yml", "prometheus/alert_rules.yml",
                    "docker-compose.yml", "grafana/provisioning/datasources/prometheus.yml",
                    "grafana/provisioning/dashboards/dashboards.yml"):
            self.assertNotIn("\t", read(rel), rel)


class ComposeTests(unittest.TestCase):
    def test_services_and_ports(self):
        text = read("docker-compose.yml")
        for svc in ("exporter:", "prometheus:", "grafana:"):
            self.assertIn(f"  {svc}", text)
        for port in ("8000:8000", "9090:9090", "3000:3000"):
            self.assertIn(port, text)

    def test_grafana_password_is_required_not_hardcoded(self):
        text = read("docker-compose.yml")
        self.assertIn("GRAFANA_ADMIN_PASSWORD:?", text)
        self.assertNotRegex(text, r"ADMIN_PASSWORD:\s*admin\b")

    def test_no_host_bind_mounts(self):
        self.assertNotIn("volumes:", read("docker-compose.yml"))


class JenkinsfileTests(unittest.TestCase):
    def test_braces_balanced(self):
        text = read("Jenkinsfile")
        self.assertEqual(text.count("{"), text.count("}"))

    def test_stages_present_in_order(self):
        text = read("Jenkinsfile")
        stages = re.findall(r"stage\('([^']+)'\)", text)
        self.assertEqual(stages, [
            "Pre-check Docker", "Unit tests", "Validate monitoring config",
            "Build images", "Deploy stack", "Smoke test",
        ])

    def test_password_comes_from_credentials(self):
        text = read("Jenkinsfile")
        self.assertIn("credentialsId: 'grafana-admin-password'", text)
        self.assertNotRegex(text, r"GRAFANA_ADMIN_PASSWORD\s*=\s*['\"]")


if __name__ == "__main__":
    unittest.main()
