# Variables for DigitalOcean Terraform configuration

variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "ssh_key_id" {
  description = "SSH key ID to use for droplets"
  type        = string
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
  default     = "nyc1"
}

variable "droplet_size" {
  description = "Droplet size slug for standard services"
  type        = string
  default     = "s-2vcpu-4gb"
}

variable "spark_droplet_size" {
  description = "Droplet size slug for Spark (needs more resources)"
  type        = string
  default     = "s-4vcpu-8gb"
}

