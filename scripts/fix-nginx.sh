#!/bin/bash
# Script para arreglar la configuración de Nginx rápidamente

set -e

echo "🔧 Arreglando configuración de Nginx..."
echo ""

# 1. Deshabilitar configuración por defecto
echo "1️⃣ Deshabilitando configuración por defecto..."
sudo rm -f /etc/nginx/sites-enabled/default
echo "✅ Default deshabilitado"
echo ""

# 2. Crear directorio si no existe
echo "2️⃣ Verificando directorios..."
sudo mkdir -p /etc/nginx/sites-available
sudo mkdir -p /etc/nginx/sites-enabled
echo "✅ Directorios verificados"
echo ""

# 3. Crear configuración si no existe
NGINX_TARGET="/etc/nginx/sites-available/rxul-chat-frontend"

if [ ! -f "$NGINX_TARGET" ]; then
    echo "3️⃣ Creando configuración de Nginx..."
    sudo tee "$NGINX_TARGET" > /dev/null << 'NGINXEOF'
server {
    listen 80;
    server_name _;
    
    root /opt/rxul-chat-frontend/dist;
    index index.html;
    
    # Servir archivos estáticos
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Cache para assets estáticos
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Proxy para API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Proxy para WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
NGINXEOF
    echo "✅ Configuración creada"
else
    echo "3️⃣ Configuración ya existe"
fi
echo ""

# 4. Activar configuración
echo "4️⃣ Activando configuración..."
sudo ln -sf "$NGINX_TARGET" /etc/nginx/sites-enabled/rxul-chat-frontend
echo "✅ Configuración activada"
echo ""

# 5. Verificar configuración
echo "5️⃣ Verificando configuración..."
if sudo nginx -t; then
    echo "✅ Configuración válida"
else
    echo "❌ Error en configuración"
    exit 1
fi
echo ""

# 6. Reiniciar Nginx
echo "6️⃣ Reiniciando Nginx..."
sudo systemctl restart nginx
echo "✅ Nginx reiniciado"
echo ""

# 7. Verificar estado
echo "7️⃣ Verificando estado..."
sudo systemctl status nginx --no-pager | head -n 5
echo ""

# 8. Probar
echo "8️⃣ Probando configuración..."
echo "   Backend directo:"
curl -s http://127.0.0.1:8000/ | head -c 100
echo ""
echo ""
echo "   Proxy de Nginx:"
curl -s http://127.0.0.1/api/ | head -c 100
echo ""
echo ""

echo "✅ ¡Configuración completada!"
echo ""
echo "Ahora puedes acceder a:"
echo "  - Frontend: http://91.98.64.119/"
echo "  - API: http://91.98.64.119/api/"

