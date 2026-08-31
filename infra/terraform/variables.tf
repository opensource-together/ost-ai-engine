variable "api_scrape_target" {
  type        = string
  description = "Prometheus scrape host:port for GET /metrics."
  default     = "host.docker.internal:8000"
}

variable "prometheus_host_port" {
  type        = number
  description = "Host port for the Terraform-managed Prometheus UI."
  default     = 9091
}

variable "grafana_host_port" {
  type        = number
  description = "Host port for the Terraform-managed Grafana UI."
  default     = 3002
}

variable "grafana_admin_password" {
  type        = string
  description = "Grafana admin password (local/dev only)."
  default     = "admin"
  sensitive   = true
}
