#!/bin/bash
# Script para arreglar permisos del frontend en la VM

set -e

echo "🔧 Arreglando permisos del frontend..."
echo ""

DEPLOY_DIR="/opt/rxul-chat-frontend/dist"

# Verificar que el directorio existe
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "❌ Error: Directorio $DEPLOY_DIR no existe"
    echo "   Creando directorio..."
    sudo mkdir -p "$DEPLOY_DIR"
fi

# Verificar si los archivos están en una subcarpeta frontend
if [ -d "$DEPLOY_DIR/frontend" ]; then
    echo "⚠️ Archivos están en subcarpeta frontend, moviendo..."
    if [ -d "$DEPLOY_DIR/frontend/dist" ]; then
        sudo mv "$DEPLOY_DIR/frontend/dist"/* "$DEPLOY_DIR/" 2>/dev/null || true
        sudo mv "$DEPLOY_DIR/frontend/dist"/.* "$DEPLOY_DIR/" 2>/dev/null || true
        sudo rmdir "$DEPLOY_DIR/frontend/dist" 2>/dev/null || true
    else
        sudo mv "$DEPLOY_DIR/frontend"/* "$DEPLOY_DIR/" 2>/dev/null || true
        sudo mv "$DEPLOY_DIR/frontend"/.* "$DEPLOY_DIR/" 2>/dev/null || true
    fi
    sudo rmdir "$DEPLOY_DIR/frontend" 2>/dev/null || true
    echo "✅ Archivos movidos a la ubicación correcta"
fi

# Verificar que hay archivos
if [ ! -f "$DEPLOY_DIR/index.html" ]; then
    echo "⚠️ Advertencia: index.html no existe"
    echo "   Contenido del directorio:"
    ls -la "$DEPLOY_DIR" || echo "   Directorio vacío"
    echo ""
    echo "   Si el directorio está vacío, necesitas hacer un nuevo deploy"
    exit 1
fi

echo "✅ Archivos encontrados"
echo ""

# Configurar permisos del directorio padre
echo "1️⃣ Configurando permisos del directorio padre..."
sudo chown -R $USER:$USER /opt/rxul-chat-frontend || true
sudo chmod 755 /opt/rxul-chat-frontend || true
echo "✅ Permisos del directorio padre configurados"
echo ""

# Configurar permisos del directorio dist
echo "2️⃣ Configurando permisos del directorio dist..."
sudo chown -R www-data:www-data "$DEPLOY_DIR"
sudo chmod 755 "$DEPLOY_DIR"
echo "✅ Permisos del directorio configurados"
echo ""

# Configurar permisos de archivos
echo "3️⃣ Configurando permisos de archivos..."
sudo find "$DEPLOY_DIR" -type f -exec chmod 644 {} \;
sudo find "$DEPLOY_DIR" -type d -exec chmod 755 {} \;
echo "✅ Permisos de archivos configurados"
echo ""

# Verificar que Nginx puede leer
echo "4️⃣ Verificando acceso de Nginx..."
if sudo -u www-data test -r "$DEPLOY_DIR/index.html"; then
    echo "✅ Nginx puede leer index.html"
else
    echo "❌ Error: Nginx NO puede leer index.html"
    echo "   Verificando permisos:"
    ls -la "$DEPLOY_DIR/index.html"
    exit 1
fi
echo ""

# Verificar configuración de Nginx
echo "5️⃣ Verificando configuración de Nginx..."
if [ -f "/etc/nginx/sites-enabled/rxul-chat-frontend" ]; then
    echo "✅ Configuración de Nginx encontrada"
    ROOT_DIR=$(grep -E "^\s*root" /etc/nginx/sites-enabled/rxul-chat-frontend | awk '{print $2}' | tr -d ';')
    echo "   Root configurado: $ROOT_DIR"
    if [ "$ROOT_DIR" = "$DEPLOY_DIR" ]; then
        echo "✅ Root coincide con el directorio de deploy"
    else
        echo "⚠️ Advertencia: Root no coincide"
    fi
else
    echo "❌ Error: Configuración de Nginx no encontrada"
fi
echo ""

# Reiniciar Nginx
echo "6️⃣ Reiniciando Nginx..."
sudo systemctl restart nginx
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx reiniciado correctamente"
else
    echo "❌ Error: Nginx no está corriendo"
    echo "   Revisa los logs: sudo journalctl -u nginx -n 20"
    exit 1
fi
echo ""

# Probar acceso local
echo "7️⃣ Probando acceso local..."
if curl -s http://127.0.0.1/ | head -c 100 > /dev/null; then
    echo "✅ Frontend accesible localmente"
else
    echo "❌ Error: Frontend NO accesible localmente"
    echo "   Revisa los logs de Nginx: sudo tail -n 20 /var/log/nginx/error.log"
    exit 1
fi
echo ""

echo "✅ ¡Permisos arreglados!"
echo ""
echo "El frontend debería estar accesible en:"
echo "  - http://91.98.64.119/"
echo ""
echo "Si aún hay problemas, verifica:"
echo "  - sudo tail -n 50 /var/log/nginx/error.log"
echo "  - ls -la $DEPLOY_DIR"
echo "  - sudo nginx -t"

