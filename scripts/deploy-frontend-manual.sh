#!/bin/bash
# Script para desplegar el frontend manualmente en la VM
# Este script compila y despliega el frontend directamente en la VM

set -e

echo "🚀 Desplegando Frontend Manualmente..."
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -d "frontend" ]; then
    echo "❌ Error: No se encontró el directorio 'frontend'"
    echo "   Asegúrate de estar en el directorio raíz del proyecto"
    exit 1
fi

cd frontend

echo "1️⃣ Instalando dependencias..."
if [ -f "package-lock.json" ]; then
    npm ci
else
    npm install
fi
echo "✅ Dependencias instaladas"
echo ""

echo "2️⃣ Compilando frontend..."
npm run build
echo "✅ Frontend compilado"
echo ""

echo "3️⃣ Creando directorio de destino..."
sudo mkdir -p /opt/rxul-chat-frontend/dist
echo "✅ Directorio creado"
echo ""

echo "4️⃣ Copiando archivos..."
sudo cp -r dist/* /opt/rxul-chat-frontend/dist/
echo "✅ Archivos copiados"
echo ""

echo "5️⃣ Ajustando permisos..."
sudo chown -R www-data:www-data /opt/rxul-chat-frontend/dist
echo "✅ Permisos ajustados"
echo ""

echo "6️⃣ Verificando archivos..."
if [ -f "/opt/rxul-chat-frontend/dist/index.html" ]; then
    echo "✅ index.html existe"
    echo "   Archivos en dist:"
    ls -la /opt/rxul-chat-frontend/dist/ | head -n 10
else
    echo "❌ Error: index.html no se copió correctamente"
    exit 1
fi
echo ""

echo "7️⃣ Reiniciando Nginx..."
sudo systemctl restart nginx
echo "✅ Nginx reiniciado"
echo ""

echo "8️⃣ Verificando acceso..."
if curl -s http://127.0.0.1/ | grep -q "html"; then
    echo "✅ Frontend accesible localmente"
else
    echo "⚠️ Frontend puede no estar accesible. Verifica la configuración de Nginx"
fi
echo ""

echo "✅ ¡Despliegue completado!"
echo ""
echo "El frontend debería estar accesible en:"
echo "  - http://91.98.64.119/"
echo ""
echo "Si no funciona, verifica:"
echo "  - sudo systemctl status nginx"
echo "  - sudo nginx -t"
echo "  - ls -la /opt/rxul-chat-frontend/dist/"

