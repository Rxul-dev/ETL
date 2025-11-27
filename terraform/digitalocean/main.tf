# Terraform configuration for DigitalOcean Production Infrastructure
# Reduced to 3 droplets to fit within DigitalOcean limits

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

# Configure the DigitalOcean Provider
provider "digitalocean" {
  token = var.do_token
}

# Variables are defined in variables.tf

# App Droplet (Backend + Frontend)
resource "digitalocean_droplet" "app_prod" {
  image    = "docker-20-04"
  name     = "app-prod"
  region   = var.region
  size     = var.droplet_size
  ssh_keys = [var.ssh_key_id]
  
  tags = ["production", "app", "backend", "frontend"]
  
  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y docker.io docker-compose nginx
    systemctl enable docker
    systemctl start docker
    systemctl enable nginx
    systemctl start nginx
  EOF
}

# Data Droplet (Metabase + Spark + Temporal)
resource "digitalocean_droplet" "data_prod" {
  image    = "docker-20-04"
  name     = "data-prod"
  region   = var.region
  size     = var.spark_droplet_size # Use larger size for Spark
  ssh_keys = [var.ssh_key_id]
  
  tags = ["production", "data", "metabase", "spark", "temporal"]
  
  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y docker.io docker-compose
    systemctl enable docker
    systemctl start docker
  EOF
}

# Monitoring Droplet (Grafana Prod + Staging)
resource "digitalocean_droplet" "monitoring_prod" {
  image    = "docker-20-04"
  name     = "monitoring-prod"
  region   = var.region
  size     = var.droplet_size
  ssh_keys = [var.ssh_key_id]
  
  tags = ["production", "monitoring", "grafana"]
  
  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y docker.io docker-compose
    systemctl enable docker
    systemctl start docker
  EOF
}

# Outputs
output "app_prod_ip" {
  value       = digitalocean_droplet.app_prod.ipv4_address
  description = "App production droplet IP (Backend + Frontend)"
}

output "data_prod_ip" {
  value       = digitalocean_droplet.data_prod.ipv4_address
  description = "Data production droplet IP (Metabase + Spark + Temporal)"
}

output "monitoring_prod_ip" {
  value       = digitalocean_droplet.monitoring_prod.ipv4_address
  description = "Monitoring production droplet IP (Grafana)"
}
