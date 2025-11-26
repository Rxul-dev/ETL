# Instrucciones de Deployment - Seguridad Aplicada

## 🚀 ¿Qué pasa cuando haces PUSH?

Cuando haces `git push origin main`, **automáticamente** se ejecuta el workflow de GitHub Actions (`.github/workflows/backend-cd.yml`) que:

1. ✅ Clona/actualiza el código en la VM (`/opt/rxul-chat-backend`)
2. ✅ Construye las imágenes Docker
3. ✅ Actualiza los contenedores con `docker-compose up -d`
4. ⚠️ **NO modifica el archivo `.env` si ya existe** (protege tus contraseñas)

## ⚠️ ACCIÓN REQUERIDA: Configurar .env en la VM

**IMPORTANTE**: Después del primer push (o si el `.env` no existe), debes conectarte a la VM y configurar las contraseñas.

### Paso 1: Conectarte a la VM

```bash
ssh usuario@91.98.64.119
```

### Paso 2: Editar el archivo .env

```bash
cd /opt/rxul-chat-backend
nano .env  # o vim, o el editor que prefieras
```

### Paso 3: Actualizar las contraseñas

El archivo `.env` debe tener estas variables con las contraseñas correctas:

```bash
# Base de datos principal
DB_PASSWORD=o$ita4070
DATABASE_URL=postgresql+psycopg2://postgres:o$ita4070@db:5432/messaging

# Data Warehouse
DW_PASSWORD=tes$a5410
WAREHOUSE_URL=postgresql://postgres:tes$a5410@dw:5432/warehouse

# Metabase
METABASE_DB_PASSWORD=met4ba$31001

# Grafana
GRAFANA_ADMIN_PASSWORD=tu_contraseña_segura_aqui

# Temporal
TEMPORAL_TARGET=temporal:7233
TEMPORAL_NAMESPACE=default

# API Base URL
API_BASE_URL=http://api:8000

# CORS (opcional)
CORS_ORIGINS=http://91.98.64.119,http://localhost:5173
```

### Paso 4: Reiniciar los contenedores

Después de actualizar el `.env`, reinicia los contenedores para que tomen las nuevas variables:

```bash
cd /opt/rxul-chat-backend
docker-compose down
docker-compose up -d
```

O simplemente:

```bash
docker-compose restart
```

## 🔒 Seguridad Aplicada

### ✅ Lo que está protegido:

1. **Puertos restringidos**: Todos los servicios internos (PostgreSQL, Prometheus, Grafana, etc.) solo escuchan en `127.0.0.1` (localhost)
2. **Solo Nginx expone puerto 80**: El único punto de entrada público es Nginx
3. **Contraseñas en variables de entorno**: No están hardcodeadas en el código
4. **Workflow no sobrescribe .env**: Si el `.env` existe, el workflow lo respeta

### 📋 Verificación Post-Deploy

Después del push, verifica que todo esté funcionando:

```bash
# En la VM
cd /opt/rxul-chat-backend

# Verificar que los contenedores estén corriendo
docker-compose ps

# Verificar que el API esté accesible (solo localhost)
curl http://127.0.0.1:8000/

# Verificar que Nginx esté sirviendo el frontend
curl http://127.0.0.1/ | head -c 100

# Ver logs si hay problemas
docker-compose logs --tail=50
```

## 🔍 Verificar Puertos Expuestos

Para confirmar que los puertos están restringidos correctamente:

```bash
# En la VM
sudo netstat -tlnp | grep LISTEN

# Deberías ver:
# - 0.0.0.0:80 (Nginx) ✅ - Único puerto público
# - 127.0.0.1:8000 (API) ✅ - Solo localhost
# - 127.0.0.1:5432 (PostgreSQL) ✅ - Solo localhost
# - 127.0.0.1:9090 (Prometheus) ✅ - Solo localhost
# - etc.
```

## 📝 Resumen

1. **Haces push** → GitHub Actions se ejecuta automáticamente
2. **El código se actualiza** en la VM automáticamente
3. **Los contenedores se reconstruyen** y actualizan automáticamente
4. **TÚ debes configurar el .env** con las contraseñas (solo la primera vez o si lo borras)

## ⚠️ Si algo falla

1. Revisa los logs de GitHub Actions en la pestaña "Actions" de tu repositorio
2. Conéctate a la VM y revisa los logs: `docker-compose logs`
3. Verifica que el `.env` tenga todas las variables necesarias
4. Verifica que los puertos estén restringidos correctamente

## ✅ Estado Actual

- ✅ Puertos restringidos a localhost
- ✅ CORS configurado
- ✅ Modo desarrollo desactivado
- ✅ Contraseñas en variables de entorno
- ✅ Workflow automático configurado
- ⚠️ **Requiere configuración manual del .env en la VM** (solo una vez)

