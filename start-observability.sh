#!/bin/bash

# Script para iniciar los servicios de observabilidad
# Uso: ./start-observability.sh

echo "🚀 Iniciando servicios de observabilidad..."

# Verificar que docker-compose esté disponible
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose no está instalado"
    exit 1
fi

# Iniciar servicios de observabilidad
echo "📊 Iniciando Prometheus, Loki, Promtail y Grafana..."
docker-compose up -d prometheus loki promtail grafana

# Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios estén listos..."
sleep 10

# Verificar estado
echo "✅ Verificando estado de los servicios..."
docker-compose ps prometheus loki promtail grafana

echo ""
echo "🎉 Servicios de observabilidad iniciados!"
echo ""
echo "📍 Accesos:"
echo "   - Grafana:      http://localhost:3001 (admin/admin)"
echo "   - Prometheus:   http://localhost:9090"
echo "   - Loki:         http://localhost:3100"
echo ""
echo "📋 Dashboards disponibles en Grafana:"
echo "   - Overview - Sistema ETL"
echo "   - API - FastAPI Metrics"
echo "   - Database - PostgreSQL Metrics"
echo "   - Apache Spark - Metrics"
echo "   - Metabase - Metrics"
echo ""

