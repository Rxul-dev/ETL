#!/bin/bash
# Script de diagnóstico para verificar la configuración de Nginx y el backend

echo "🔍 Diagnóstico de Nginx y Backend"
echo "=================================="
echo ""

echo "1️⃣ Verificando si Nginx está corriendo..."
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx está corriendo"
else
    echo "❌ Nginx NO está corriendo"
    echo "   Ejecuta: sudo systemctl start nginx"
fi
echo ""

echo "2️⃣ Verificando configuración de Nginx..."
if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Configuración de Nginx es válida"
    sudo nginx -t
else
    echo "❌ Configuración de Nginx tiene errores:"
    sudo nginx -t
fi
echo ""

echo "3️⃣ Verificando si el backend está corriendo en el puerto 8000..."
if curl -s http://127.0.0.1:8000/ > /dev/null; then
    echo "✅ Backend responde en el puerto 8000"
    echo "   Respuesta:"
    curl -s http://127.0.0.1:8000/ | head -c 100
    echo ""
else
    echo "❌ Backend NO responde en el puerto 8000"
    echo "   Verifica que el backend esté corriendo:"
    echo "   - Si usas Docker: docker ps | grep 8000"
    echo "   - Si usas docker-compose: cd /opt/rxul-chat-backend && docker-compose ps"
fi
echo ""

echo "4️⃣ Verificando configuración activa de Nginx..."
if [ -f /etc/nginx/sites-enabled/rxul-chat-frontend ]; then
    echo "✅ Configuración rxul-chat-frontend está activa"
    echo "   Archivo: /etc/nginx/sites-enabled/rxul-chat-frontend"
else
    echo "❌ Configuración rxul-chat-frontend NO está activa"
    echo "   Verifica: ls -la /etc/nginx/sites-enabled/"
fi
echo ""

echo "5️⃣ Verificando archivos del frontend..."
if [ -d /opt/rxul-chat-frontend/dist ] && [ -f /opt/rxul-chat-frontend/dist/index.html ]; then
    echo "✅ Archivos del frontend existen"
    echo "   Archivos encontrados: $(ls /opt/rxul-chat-frontend/dist/ | wc -l)"
else
    echo "❌ Archivos del frontend NO existen"
    echo "   Verifica: ls -la /opt/rxul-chat-frontend/dist/"
fi
echo ""

echo "6️⃣ Verificando proxy de API a través de Nginx..."
if curl -s http://127.0.0.1/api/ > /dev/null; then
    echo "✅ Proxy de API funciona localmente"
    echo "   Respuesta:"
    curl -s http://127.0.0.1/api/ | head -c 100
    echo ""
else
    echo "❌ Proxy de API NO funciona localmente"
    echo "   Esto indica un problema con la configuración de Nginx"
fi
echo ""

echo "7️⃣ Verificando logs de Nginx (últimas 10 líneas)..."
echo "   Error log:"
sudo tail -n 10 /var/log/nginx/error.log 2>/dev/null || echo "   No hay errores recientes"
echo ""

echo "8️⃣ Verificando procesos de Docker..."
if command -v docker &> /dev/null; then
    echo "   Contenedores corriendo:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "   Docker no está disponible o no hay permisos"
else
    echo "   Docker no está instalado"
fi
echo ""

echo "=================================="
echo "✅ Diagnóstico completado"

