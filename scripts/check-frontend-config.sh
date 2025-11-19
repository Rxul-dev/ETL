#!/bin/bash
# Script para verificar la configuración del frontend en la VM

echo "=== Verificación de Configuración del Frontend ==="
echo ""

# Verificar que los archivos estén desplegados
echo "1. Verificando archivos desplegados..."
if [ -d "/opt/rxul-chat-frontend/dist" ]; then
    echo "✅ Directorio /opt/rxul-chat-frontend/dist existe"
    echo "   Archivos encontrados:"
    ls -la /opt/rxul-chat-frontend/dist/ | head -5
else
    echo "❌ Directorio /opt/rxul-chat-frontend/dist no existe"
    exit 1
fi

echo ""
echo "2. Buscando referencias a localhost:8000 en el código compilado..."
if grep -r "localhost:8000" /opt/rxul-chat-frontend/dist/ 2>/dev/null | head -3; then
    echo "⚠️  ADVERTENCIA: Se encontraron referencias a localhost:8000"
    echo "   Esto indica que el build no se hizo correctamente en modo producción"
else
    echo "✅ No se encontraron referencias a localhost:8000"
fi

echo ""
echo "3. Buscando referencias a /api en el código compilado..."
if grep -r '"/api"' /opt/rxul-chat-frontend/dist/ 2>/dev/null | head -3; then
    echo "✅ Se encontraron referencias a /api (correcto para producción)"
else
    echo "⚠️  No se encontraron referencias a /api"
fi

echo ""
echo "4. Verificando configuración de Nginx..."
if [ -f "/etc/nginx/sites-enabled/rxul-chat-frontend" ]; then
    echo "✅ Configuración de Nginx encontrada"
    echo "   Proxy /api configurado:"
    grep -A 2 "location /api" /etc/nginx/sites-enabled/rxul-chat-frontend | head -3
else
    echo "❌ Configuración de Nginx no encontrada"
fi

echo ""
echo "5. Verificando que el backend esté accesible..."
if curl -s http://127.0.0.1:8000/ > /dev/null; then
    echo "✅ Backend accesible en http://127.0.0.1:8000"
else
    echo "❌ Backend NO accesible en http://127.0.0.1:8000"
fi

echo ""
echo "6. Verificando proxy de Nginx..."
if curl -s http://127.0.0.1/api/ > /dev/null; then
    echo "✅ Proxy de Nginx funcionando (http://127.0.0.1/api/)"
else
    echo "❌ Proxy de Nginx NO funcionando"
fi

echo ""
echo "=== Fin de la verificación ==="
echo ""
echo "Si el frontend sigue usando localhost:8000:"
echo "1. Verifica que el secret VITE_API_URL en GitHub esté vacío o no exista"
echo "2. Haz un nuevo commit y push a main para que se ejecute el workflow de CD"
echo "3. Espera a que el workflow termine y verifica los logs"
echo "4. Revisa la consola del navegador para ver los logs de [API Config]"

