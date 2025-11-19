#!/bin/bash
# Script para arreglar la estructura del frontend (mover archivos de subcarpeta)

set -e

echo "🔧 Arreglando estructura del frontend..."
echo ""

DEPLOY_DIR="/opt/rxul-chat-frontend/dist"

# Verificar que el directorio existe
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "❌ Error: Directorio $DEPLOY_DIR no existe"
    exit 1
fi

# Verificar si los archivos están en una subcarpeta frontend
if [ -d "$DEPLOY_DIR/frontend" ]; then
    echo "⚠️ Archivos están en subcarpeta frontend, moviendo..."
    
    # Verificar si hay una subcarpeta dist dentro de frontend
    if [ -d "$DEPLOY_DIR/frontend/dist" ]; then
        echo "   Moviendo archivos de frontend/dist/ a dist/"
        sudo mv "$DEPLOY_DIR/frontend/dist"/* "$DEPLOY_DIR/" 2>/dev/null || true
        sudo mv "$DEPLOY_DIR/frontend/dist"/.* "$DEPLOY_DIR/" 2>/dev/null || true
        sudo rmdir "$DEPLOY_DIR/frontend/dist" 2>/dev/null || true
    else
        echo "   Moviendo archivos de frontend/ a dist/"
        sudo mv "$DEPLOY_DIR/frontend"/* "$DEPLOY_DIR/" 2>/dev/null || true
        sudo mv "$DEPLOY_DIR/frontend"/.* "$DEPLOY_DIR/" 2>/dev/null || true
    fi
    
    # Eliminar carpeta frontend vacía
    sudo rmdir "$DEPLOY_DIR/frontend" 2>/dev/null || true
    echo "✅ Archivos movidos a la ubicación correcta"
fi

# Verificar que index.html existe ahora
if [ -f "$DEPLOY_DIR/index.html" ]; then
    echo "✅ index.html encontrado en la ubicación correcta"
    echo ""
    echo "📋 Contenido del directorio:"
    ls -la "$DEPLOY_DIR" | head -10
else
    echo "❌ Error: index.html aún no existe"
    echo "   Contenido del directorio:"
    ls -la "$DEPLOY_DIR"
    exit 1
fi

# Configurar permisos
echo ""
echo "🔧 Configurando permisos..."
sudo chown -R www-data:www-data "$DEPLOY_DIR"
sudo chmod -R 755 "$DEPLOY_DIR"
sudo find "$DEPLOY_DIR" -type f -exec chmod 644 {} \;
sudo find "$DEPLOY_DIR" -type d -exec chmod 755 {} \;
echo "✅ Permisos configurados"

# Reiniciar Nginx
echo ""
echo "🔄 Reiniciando Nginx..."
sudo systemctl restart nginx
echo "✅ Nginx reiniciado"

echo ""
echo "✅ ¡Estructura arreglada!"
echo ""
echo "El frontend debería estar accesible en:"
echo "  - http://91.98.64.119/"

