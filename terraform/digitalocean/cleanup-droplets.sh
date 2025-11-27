#!/bin/bash

# Script para limpiar droplets existentes en DigitalOcean
# Uso: ./cleanup-droplets.sh

set -e

echo "🧹 Limpiando droplets existentes en DigitalOcean"
echo ""

# Verificar que terraform está inicializado
if [ ! -d ".terraform" ]; then
    echo "⚠️ Terraform no está inicializado. Ejecuta 'terraform init' primero."
    exit 1
fi

# Verificar que terraform.tfvars existe
if [ ! -f "terraform.tfvars" ]; then
    echo "⚠️ terraform.tfvars no existe. Crea el archivo primero."
    exit 1
fi

echo "📋 Droplets existentes que se destruirán:"
terraform state list | grep "digitalocean_droplet" || echo "No hay droplets en el estado de Terraform"

echo ""
read -p "¿Estás seguro de que quieres destruir todos los droplets? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Operación cancelada"
    exit 0
fi

echo ""
echo "🗑️  Destruyendo droplets..."
terraform destroy -auto-approve

echo ""
echo "✅ Limpieza completada"

