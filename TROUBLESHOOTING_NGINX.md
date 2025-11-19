# Solución de Problemas: Nginx y Backend

## Problema: 404 en `/api/`

Si recibes un error 404 al acceder a `http://91.98.64.119/api/`, sigue estos pasos:

## Diagnóstico Rápido

### 1. Verificar que el backend está corriendo

Conéctate a tu VM por SSH y ejecuta:

```bash
# Si usas Docker Compose
cd /opt/rxul-chat-backend
docker-compose ps

# Verificar que el puerto 8000 está escuchando
curl http://127.0.0.1:8000/
```

**Deberías ver:** `{"ok":true,"service":"Rxul-chat"}`

Si no ves esto, el backend no está corriendo. Inícialo con:

```bash
cd /opt/rxul-chat-backend
docker-compose up -d
```

### 2. Verificar configuración de Nginx

```bash
# Verificar que Nginx está corriendo
sudo systemctl status nginx

# Verificar configuración
sudo nginx -t

# Ver configuración activa
ls -la /etc/nginx/sites-enabled/

# Ver contenido de la configuración
cat /etc/nginx/sites-enabled/rxul-chat-frontend
```

**Asegúrate de que:**
- Nginx está corriendo (`active (running)`)
- La configuración es válida (`test is successful`)
- Existe el archivo `rxul-chat-frontend` en `sites-enabled`

### 3. Verificar que el proxy funciona localmente

```bash
# Desde la VM, probar el proxy localmente
curl http://127.0.0.1/api/
```

**Deberías ver:** `{"ok":true,"service":"Rxul-chat"}`

Si ves 404 aquí, el problema es la configuración de Nginx.

### 4. Verificar logs de Nginx

```bash
# Ver errores recientes
sudo tail -n 50 /var/log/nginx/error.log

# Ver accesos
sudo tail -n 50 /var/log/nginx/access.log
```

## Soluciones Comunes

### Solución 1: Backend no está corriendo

```bash
cd /opt/rxul-chat-backend
docker-compose up -d
docker-compose logs -f
```

### Solución 2: Nginx no está usando la configuración correcta

```bash
# Eliminar configuración por defecto
sudo rm -f /etc/nginx/sites-enabled/default

# Asegurar que nuestra configuración está activa
sudo ln -sf /etc/nginx/sites-available/rxul-chat-frontend /etc/nginx/sites-enabled/rxul-chat-frontend

# Verificar y reiniciar
sudo nginx -t
sudo systemctl restart nginx
```

### Solución 3: Re-aplicar configuración de Nginx

Si el workflow de CD no aplicó la configuración correctamente:

```bash
# Copiar manualmente la configuración
sudo cp /tmp/rxul-chat-frontend.conf /etc/nginx/sites-available/rxul-chat-frontend

# O descargarla del repositorio si tienes git
cd /opt/rxul-chat-backend  # o donde tengas el repo
sudo cp nginx/rxul-chat-frontend.conf /etc/nginx/sites-available/rxul-chat-frontend

# Activar y reiniciar
sudo ln -sf /etc/nginx/sites-available/rxul-chat-frontend /etc/nginx/sites-enabled/rxul-chat-frontend
sudo nginx -t
sudo systemctl restart nginx
```

### Solución 4: Verificar firewall

```bash
# Verificar que el puerto 80 está abierto
sudo ufw status

# Si no está abierto, abrirlo
sudo ufw allow 80/tcp
sudo ufw allow 8000/tcp  # Para acceso directo al backend si es necesario
```

## Script de Diagnóstico Automático

Puedes usar el script de diagnóstico:

```bash
# Desde tu máquina local, copiar el script a la VM
scp scripts/diagnose-nginx.sh usuario@91.98.64.119:/tmp/

# En la VM, ejecutar
chmod +x /tmp/diagnose-nginx.sh
sudo /tmp/diagnose-nginx.sh
```

## Verificación Final

Después de aplicar las soluciones, verifica:

1. ✅ Backend responde: `curl http://127.0.0.1:8000/`
2. ✅ Nginx está corriendo: `sudo systemctl status nginx`
3. ✅ Proxy funciona: `curl http://127.0.0.1/api/`
4. ✅ Frontend accesible: `curl http://127.0.0.1/` (debería mostrar HTML)
5. ✅ Desde fuera: `curl http://91.98.64.119/api/`

## Estructura Esperada

```
/etc/nginx/
├── sites-available/
│   └── rxul-chat-frontend  ← Configuración principal
└── sites-enabled/
    └── rxul-chat-frontend  ← Symlink a sites-available

/opt/rxul-chat-frontend/
└── dist/  ← Archivos compilados del frontend
    └── index.html

/opt/rxul-chat-backend/
├── docker-compose.yml
└── ...  ← Backend corriendo en puerto 8000
```

## Contacto

Si el problema persiste después de seguir estos pasos, verifica:
- Los logs del workflow de GitHub Actions
- Los logs de Docker: `docker-compose logs`
- Los logs de Nginx: `sudo tail -f /var/log/nginx/error.log`

