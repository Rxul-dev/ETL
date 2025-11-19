#!/bin/bash
echo "🔍 Verificando estado de Nginx..."
echo ""

echo "1. Estado de Nginx:"
sudo systemctl status nginx --no-pager | head -n 10
echo ""

echo "2. Configuración activa:"
ls -la /etc/nginx/sites-enabled/
echo ""

echo "3. Verificando configuración:"
sudo nginx -t
echo ""

echo "4. Probando backend directamente:"
curl -s http://127.0.0.1:8000/ | head -c 200
echo ""
echo ""

echo "5. Probando proxy de Nginx:"
curl -s http://127.0.0.1/api/ | head -c 200
echo ""
echo ""

echo "6. Contenido de configuración activa:"
if [ -f /etc/nginx/sites-enabled/rxul-chat-frontend ]; then
    echo "✅ Archivo existe:"
    cat /etc/nginx/sites-enabled/rxul-chat-frontend
elif [ -f /etc/nginx/sites-enabled/default ]; then
    echo "⚠️ Solo existe default:"
    cat /etc/nginx/sites-enabled/default | head -n 30
else
    echo "❌ No hay configuración activa"
fi

