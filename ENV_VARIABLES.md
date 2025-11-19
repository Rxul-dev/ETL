# Variables de Entorno

Este documento describe las variables de entorno necesarias para el proyecto.

## Backend

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```bash
# Base de datos principal (PostgreSQL)
# Formato: postgresql+psycopg2://usuario:contraseña@host:puerto/nombre_db
# Por defecto: postgresql+psycopg2://postgres:postgres@localhost:5432/messaging
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/messaging

# Data Warehouse (Opcional - solo si usas ETL)
# Formato: postgresql://usuario:contraseña@host:puerto/nombre_db
# Si no lo configuras, el ETL no funcionará
WAREHOUSE_URL=postgresql://postgres:postgres@localhost:5440/warehouse

# Temporal (Opcional - solo si usas workflows de Temporal)
# Por defecto: temporal:7233
TEMPORAL_TARGET=temporal:7233
TEMPORAL_NAMESPACE=default

# URL base de la API (opcional)
API_BASE_URL=http://api:8000
```

### Variables Requeridas

- **`DATABASE_URL`**: URL de conexión a la base de datos PostgreSQL principal. Si no se configura, usa el valor por defecto.

### Variables Opcionales

- **`WAREHOUSE_URL`**: URL de conexión al Data Warehouse (para ETL). Si no se configura, el ETL no funcionará.
- **`TEMPORAL_TARGET`**: URL del servidor Temporal (para workflows).
- **`TEMPORAL_NAMESPACE`**: Namespace de Temporal (por defecto: `default`).
- **`API_BASE_URL`**: URL base de la API (usado internamente).

## Frontend

Para el frontend, las variables de entorno se configuran de forma diferente:

### Desarrollo Local

En desarrollo, **NO necesitas configurar nada**. El proxy de Vite maneja automáticamente las conexiones al backend en `http://localhost:8000`.

### Producción

Si estás haciendo build para producción, puedes crear un archivo `.env` en la carpeta `frontend/` con:

```bash
# URL de la API para el frontend (solo necesario en producción)
# Ejemplo: https://api.tudominio.com o http://tu-servidor:8000
VITE_API_URL=http://localhost:8000
```

**Nota**: Las variables de entorno en Vite deben comenzar con `VITE_` para ser accesibles en el código del frontend.

## GitHub Secrets (Para CI/CD)

Para que el deployment automático funcione, configura estos secrets en GitHub (Settings > Secrets and variables > Actions):

### Requeridos para Deployment

- **`HETZNER_HOST`**: IP o dominio del servidor Hetzner (ej: `123.45.67.89` o `servidor.tudominio.com`)
- **`HETZNER_USER`**: Usuario SSH para conectarse al servidor (ej: `root` o `deploy`)
- **`HETZNER_SSH_KEY`**: Clave privada SSH para autenticación

### Opcionales

- **`VITE_API_URL`**: URL de la API para el build del frontend en producción (ej: `https://api.tudominio.com`)

## Ejemplo de `.env` para Desarrollo Local

```bash
# Backend
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/messaging
WAREHOUSE_URL=postgresql://postgres:postgres@localhost:5440/warehouse
TEMPORAL_TARGET=temporal:7233
TEMPORAL_NAMESPACE=default
```

**Nota**: Si usas Docker Compose, estas variables ya están configuradas en `docker-compose.yml`, así que no necesitas crear un `.env` a menos que quieras sobrescribir los valores por defecto.

