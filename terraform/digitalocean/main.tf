# Terraform configuration for DigitalOcean Production Infrastructure
# This creates droplets for each service in production

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
  
  # Optional: Use remote state backend
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "production/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# Configure the DigitalOcean Provider
provider "digitalocean" {
  token = var.do_token
}

# Variables are defined in variables.tf

# Backend Droplet (Production)
resource "digitalocean_droplet" "backend_prod" {
  image    = "docker-20-04"
  name     = "backend-prod"
  region   = var.region
  size     = var.droplet_size
  ssh_keys = [var.ssh_key_id]
  
  tags = ["production", "backend"]
  
  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y docker.io docker-compose
    systemctl enable docker
    systemctl start docker
  EOF
}

# Frontend Droplet (Production)
resource "digitalocean_droplet" "frontend_prod" {
  image    = "docker-20-04"
  name     = "frontend-prod"
  region   = var.region
  size     = var.droplet_size
  ssh_keys = [var.ssh_key_id]
  
  tags = ["production", "frontend"]
  
  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y nginx docker.io
    systemctl enable nginx
    systemctl start nginx
  EOF
}

# Metabase Droplet (Production)
resource "digitalocean_droplet" "metabase_prod" {
  image    = "docker-20-04"
  name     = "metabase-prod"
  region   = var.region
  size     = var.droplet_size
  ssh_keys = [var.ssh_key_id]
  
  tags = ["production", "metabase"]
  
  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y docker.io docker-compose
    systemctl enable docker
    systemctl start docker
  EOF
}

# Spark Droplet (Production)
resource "digitalocean_droplet" "spark_prod" {
  image    = "docker-20-04"
  name     = "spark-prod"
  region   = var.region
  size     = var.spark_droplet_size # Use variable for Spark size
  ssh_keys = [var.ssh_key_id]
  
  tags = ["production", "spark"]
  
  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y docker.io docker-compose
    systemctl enable docker
    systemctl start docker
  EOF
}

# Temporal Droplet (Production)
resource "digitalocean_droplet" "temporal_prod" {
  image    = "docker-20-04"
  name     = "temporal-prod"
  region   = var.region
  size     = var.droplet_size
  ssh_keys = [var.ssh_key_id]
  
  tags = ["production", "temporal"]
  
  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y docker.io docker-compose
    systemctl enable docker
    systemctl start docker
  EOF
}

# Grafana Production Droplet
resource "digitalocean_droplet" "grafana_prod" {
  image    = "docker-20-04"
  name     = "grafana-prod"
  region   = var.region
  size     = var.droplet_size
  ssh_keys = [var.ssh_key_id]
  
  tags = ["production", "grafana", "monitoring"]
  
  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y docker.io docker-compose
    systemctl enable docker
    systemctl start docker
  EOF
}

# Grafana Staging Droplet (Separate from production for security)
resource "digitalocean_droplet" "grafana_staging" {
  image    = "docker-20-04"
  name     = "grafana-staging"
  region   = var.region
  size     = var.droplet_size
  ssh_keys = [var.ssh_key_id]
  
  tags = ["staging", "grafana", "monitoring"]
  
  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y docker.io docker-compose
    systemctl enable docker
    systemctl start docker
  EOF
}

# Outputs
output "backend_prod_ip" {
  value       = digitalocean_droplet.backend_prod.ipv4_address
  description = "Backend production droplet IP"
}

output "frontend_prod_ip" {
  value       = digitalocean_droplet.frontend_prod.ipv4_address
  description = "Frontend production droplet IP"
}

output "metabase_prod_ip" {
  value       = digitalocean_droplet.metabase_prod.ipv4_address
  description = "Metabase production droplet IP"
}

output "spark_prod_ip" {
  value       = digitalocean_droplet.spark_prod.ipv4_address
  description = "Spark production droplet IP"
}

output "temporal_prod_ip" {
  value       = digitalocean_droplet.temporal_prod.ipv4_address
  description = "Temporal production droplet IP"
}

output "grafana_prod_ip" {
  value       = digitalocean_droplet.grafana_prod.ipv4_address
  description = "Grafana production droplet IP"
}

output "grafana_staging_ip" {
  value       = digitalocean_droplet.grafana_staging.ipv4_address
  description = "Grafana staging droplet IP"
}

