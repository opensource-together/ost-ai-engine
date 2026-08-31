locals {
  repo_root = abspath("${path.module}/../..")
}

resource "docker_network" "observability" {
  name = "ost-linker-observability"
}

resource "local_file" "prometheus_config" {
  filename = "${path.module}/.generated/prometheus.yml"
  content = templatefile("${path.module}/prometheus.yml.tftpl", {
    scrape_target = var.api_scrape_target
  })
}

resource "docker_image" "prometheus" {
  name         = "prom/prometheus:v2.55.1"
  keep_locally = true
}

resource "docker_image" "grafana" {
  name         = "grafana/grafana:11.4.0"
  keep_locally = true
}

resource "docker_container" "prometheus" {
  name  = "ost-linker-prometheus-tf"
  image = docker_image.prometheus.image_id

  networks_advanced {
    name    = docker_network.observability.name
    aliases = ["prometheus"]
  }

  host {
    host = "host.docker.internal"
    ip   = "host-gateway"
  }

  ports {
    internal = 9090
    external = var.prometheus_host_port
  }

  mounts {
    type      = "bind"
    source    = abspath(local_file.prometheus_config.filename)
    target    = "/etc/prometheus/prometheus.yml"
    read_only = true
  }

  mounts {
    type      = "bind"
    source    = "${local.repo_root}/observability/prometheus/rules.yml"
    target    = "/etc/prometheus/rules.yml"
    read_only = true
  }

  command = ["--config.file=/etc/prometheus/prometheus.yml"]

  restart = "unless-stopped"
}

resource "docker_container" "grafana" {
  name  = "ost-linker-grafana-tf"
  image = docker_image.grafana.image_id

  networks_advanced {
    name = docker_network.observability.name
  }

  ports {
    internal = 3000
    external = var.grafana_host_port
  }

  env = [
    "GF_SECURITY_ADMIN_USER=admin",
    "GF_SECURITY_ADMIN_PASSWORD=${var.grafana_admin_password}",
    "GF_USERS_DEFAULT_THEME=dark",
  ]

  mounts {
    type      = "bind"
    source    = "${local.repo_root}/observability/grafana/provisioning"
    target    = "/etc/grafana/provisioning"
    read_only = true
  }

  mounts {
    type      = "bind"
    source    = "${local.repo_root}/observability/grafana/dashboards"
    target    = "/var/lib/grafana/dashboards"
    read_only = true
  }

  restart = "unless-stopped"
}
