# ETL de Mensajería (Extract → Transform → Load)

Este ETL consume el API (GET paginados a 250 ítems), transforma y carga en un **data warehouse** Postgres.

## Tablas destino (DW)
- `dim_users`: catálogo de usuarios
- `dim_chats`: catálogo de chats
- `bridge_chat_members`: relación N–M entre usuarios y chats
- `fact_messages`: hechos de mensajes con campos derivados (`message_length`, `created_day`, `created_hour`)

## Cómo correrlo

### 1) Agregar el servicio de DW en Docker
Actualiza tu `docker-compose.yml` para incluir un Postgres para el warehouse:

```yaml
services:
  dw:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: warehouse
    ports:
      - "5440:5432"
    volumes:
      - pgdata_dw:/var/lib/postgresql/data
volumes:
  pgdata_dw:
```

> Nota: El API ya corre en `api` y Postgres del app en `db`. El DW es `dw`.

### 2) Variables de entorno
Copia `.env.example` a `.env` y ajusta si es necesario:
```
API_BASE_URL=http://api:8000
WAREHOUSE_URL=postgresql://postgres:postgres@dw:5432/warehouse
```

### 3) Instalar y levantar
```bash
docker compose up -d --build
```

### 4) Ejecutar el ETL
```bash
docker compose exec api python etl/run_etl.py
```

El script es **idempotente**: usa `CREATE TABLE IF NOT EXISTS` y `ON CONFLICT ... DO UPDATE` para upsert.

## Cómo funciona
- **Extract**: llama a `/users`, `/chats`, `/chats/{id}/members`, `/chats/{id}/messages` usando paginación (`page_size=250`) hasta agotar `total`.

- **Transform**: calcula `message_length`, `created_day`, `created_hour`; mantiene ids originales.

- **Load**: inserta/actualiza en tablas DW en lote con `execute_batch`.


## Pruebas
1. Ejecuta `seed.py` para tener datos.

2. Corre el ETL y verifica conteos en DW:

```bash
docker compose exec dw psql -U postgres -d warehouse -c "SELECT count(*) FROM fact_messages;"
```
