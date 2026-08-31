output "prometheus_url" {
  value = "http://127.0.0.1:${var.prometheus_host_port}"
}

output "grafana_url" {
  value = "http://127.0.0.1:${var.grafana_host_port}"
}
