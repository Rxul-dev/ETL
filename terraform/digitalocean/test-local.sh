#!/bin/bash

# Script para probar Terraform localmente antes de aplicar
# Uso: ./test-local.sh

set -e

echo "🧪 Probando configuración de Terraform para DigitalOcean"
echo ""

# Verificar que terraform está instalado
if ! command -v terraform &> /dev/null; then
    echo "❌ Error: Terraform no está instalado"
    echo "Instala con: brew install terraform"
    exit 1
fi

# Verificar que existe terraform.tfvars
if [ ! -f "terraform.tfvars" ]; then
    echo "⚠️  No existe terraform.tfvars"
    echo ""
    echo "Crea el archivo con:"
    echo ""
    echo "cat > terraform.tfvars << EOF"
    echo "do_token   = \"tu-token-de-digitalocean\""
    echo "ssh_key_id = \"tu-ssh-key-id\""
    echo "region     = \"nyc1\""
    echo "EOF"
    echo ""
    echo "⚠️  IMPORTANTE: NO commitees terraform.tfvars (está en .gitignore)"
    exit 1
fi

echo "✅ terraform.tfvars encontrado"
echo ""

# Inicializar Terraform
echo "📦 Inicializando Terraform..."
terraform init

echo ""
echo "🔍 Ejecutando terraform plan (dry run)..."
echo "Esto mostrará qué recursos se crearían SIN aplicarlos"
echo ""

terraform plan

echo ""
echo "✅ Plan completado"
echo ""
echo "📋 Próximos pasos:"
echo "  1. Revisa el plan arriba"
echo "  2. Si todo se ve bien, puedes aplicar con: terraform apply"
echo "  3. ⚠️  terraform apply creará recursos reales que cuestan dinero"
echo ""
echo "💡 Para aplicar vía GitHub Actions (recomendado):"
echo "  1. Configura los secrets en GitHub: DO_TOKEN y DO_SSH_KEY_ID"
echo "  2. Haz push a main"
echo "  3. El workflow aplicará Terraform automáticamente"

