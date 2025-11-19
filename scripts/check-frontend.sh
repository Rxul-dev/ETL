#!/bin/bash
echo "🔍 Verificando estado del Frontend..."
echo ""

echo "1. Verificando directorio del frontend:"
if [ -d "/opt/rxul-chat-frontend/dist" ]; then
    echo "✅ Directorio existe: /opt/rxul-chat-frontend/dist"
    echo "   Archivos encontrados:"
    ls -la /opt/rxul-chat-frontend/dist/ | head -n 10
    echo ""
    
    if [ -f "/opt/rxul-chat-frontend/dist/index.html" ]; then
        echo "✅ index.html existe"
        echo "   Tamaño: $(du -h /opt/rxul-chat-frontend/dist/index.html | cut -f1)"
    else
        echo "❌ index.html NO existe"
    fi
else
    echo "❌ Directorio NO existe: /opt/rxul-chat-frontend/dist"
    echo "   El frontend no ha sido desplegado aún"
fi
echo ""

echo "2. Verificando Nginx:"
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx está corriendo"
else
    echo "❌ Nginx NO está corriendo"
fi
echo ""

echo "3. Verificando configuración de Nginx:"
if [ -f "/etc/nginx/sites-enabled/rxul-chat-frontend" ]; then
    echo "✅ Configuración activa"
    echo "   Root configurado:"
    grep -E "^\s*root" /etc/nginx/sites-enabled/rxul-chat-frontend || echo "   No se encontró 'root'"
else
    echo "❌ Configuración NO activa"
fi
echo ""

echo "4. Probando acceso local:"
if curl -s http://127.0.0.1/ | head -c 200 > /dev/null; then
    echo "✅ Frontend responde localmente"
    echo "   Primeros 200 caracteres:"
    curl -s http://127.0.0.1/ | head -c 200
    echo ""
else
    echo "❌ Frontend NO responde localmente"
fi
echo ""

echo "5. Verificando permisos:"
if [ -d "/opt/rxul-chat-frontend/dist" ]; then
    ls -ld /opt/rxul-chat-frontend/dist
    echo "   Propietario debería ser www-data o el usuario actual"
fi
echo ""

echo "=================================="
echo "Resumen:"
if [ -f "/opt/rxul-chat-frontend/dist/index.html" ] && systemctl is-active --quiet nginx; then
    echo "✅ Frontend debería estar accesible en http://91.98.64.119/"
else
    echo "❌ Frontend NO está listo. Necesitas:"
    if [ ! -f "/opt/rxul-chat-frontend/dist/index.html" ]; then
        echo "   - Desplegar el frontend (ejecutar workflow de frontend CD)"
    fi
    if ! systemctl is-active --quiet nginx; then
        echo "   - Iniciar Nginx: sudo systemctl start nginx"
    fi
fi

