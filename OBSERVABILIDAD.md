# Observabilidad del Sistema ETL

Este proyecto incluye un stack completo de observabilidad usando **Grafana**, **Prometheus** y **Loki** para monitorear todos los servicios del sistema.

## Componentes

### Prometheus
- **Puerto**: 9090
- **URL**: http://localhost:9090
- **Función**: Recopila y almacena métricas de todos los servicios

### Loki
- **Puerto**: 3100
- **URL**: http://localhost:3100
- **Función**: Agrega y almacena logs de todos los servicios

### Promtail
- **Función**: Recolector de logs que envía los logs a Loki

### Grafana
- **Puerto**: 3001
- **URL**: http://localhost:3001
- **Credenciales por defecto**:
  - Usuario: `admin`
  - Contraseña: `admin`

## Servicios Monitoreados

### 1. API (FastAPI)
- **Métricas**: Request rate, latencia, errores, conexiones activas
- **Dashboard**: `API - FastAPI Metrics`
- **Endpoint de métricas**: http://api:8000/metrics

### 2. Base de Datos (PostgreSQL)
Se monitorean tres instancias de PostgreSQL:
- **DB Principal** (messaging): Puerto 5432
- **Data Warehouse** (warehouse): Puerto 5440
- **Metabase DB**: Puerto interno

**Métricas incluidas**:
- Conexiones activas
- Transacciones por segundo
- Tamaño de base de datos
- Cache hit ratio
- Queries activas
- Dead tuples

**Dashboard**: `Database - PostgreSQL Metrics`

### 3. Apache Spark
- **Spark Master UI**: http://localhost:8081
- **Métricas**: Aplicaciones activas, workers, cores, memoria
- **Dashboard**: `Apache Spark - Metrics`

**Nota**: Spark no expone métricas Prometheus por defecto. El dashboard está preparado para cuando se configure un exporter o se habilite la exposición de métricas Prometheus en Spark.

### 4. Metabase
- **UI**: http://localhost:3000
- **Métricas**: Sesiones activas, queries, duración de consultas
- **Dashboard**: `Metabase - Metrics`

**Nota**: Metabase no expone métricas Prometheus por defecto. Se puede monitorear a través de logs y métricas de su base de datos.

### 5. Sistema (Node Exporter)
- **Métricas**: CPU, memoria, disco, red
- **Puerto**: 9100

## Dashboards Disponibles

1. **Overview - Sistema ETL**: Vista general del sistema
2. **API - FastAPI Metrics**: Métricas detalladas de la API
3. **Database - PostgreSQL Metrics**: Métricas de todas las bases de datos
4. **Apache Spark - Metrics**: Métricas de Spark (requiere configuración adicional)
5. **Metabase - Metrics**: Métricas de Metabase (requiere configuración adicional)

## Inicio Rápido

1. **Iniciar todos los servicios**:
```bash
docker-compose up -d
```

2. **Verificar que los servicios estén corriendo**:
```bash
docker-compose ps
```

3. **Acceder a Grafana**:
   - Abrir http://localhost:3001
   - Login con `admin`/`admin`
   - Los dashboards se cargarán automáticamente

4. **Acceder a Prometheus**:
   - Abrir http://localhost:9090
   - Verificar targets en Status > Targets

5. **Verificar logs en Loki**:
   - En Grafana, ir a Explore
   - Seleccionar datasource "Loki"
   - Hacer queries como: `{service="api"}`

## Configuración de Logs

Los logs se recopilan automáticamente de todos los contenedores Docker usando Promtail. Los logs están etiquetados por servicio y se pueden filtrar en Grafana usando:

- `{service="api"}` - Logs de la API
- `{service="db"}` - Logs de la base de datos principal
- `{service="dw"}` - Logs del data warehouse
- `{service="spark-master"}` - Logs de Spark Master
- `{service="spark-worker"}` - Logs de Spark Worker
- `{service="metabase"}` - Logs de Metabase

## Métricas Personalizadas

### API FastAPI
La API está instrumentada con `prometheus-fastapi-instrumentator` que expone automáticamente:
- `http_requests_total`: Total de requests
- `http_request_duration_seconds`: Duración de requests
- `http_requests_in_progress`: Requests en progreso

### PostgreSQL
Los exporters de PostgreSQL exponen métricas estándar como:
- `pg_stat_database_*`: Estadísticas de base de datos
- `pg_stat_activity_*`: Actividad de conexiones
- `pg_database_size_bytes`: Tamaño de bases de datos

## Troubleshooting

### Prometheus no puede scrapear un servicio
1. Verificar que el servicio esté corriendo: `docker-compose ps`
2. Verificar conectividad: `docker-compose exec prometheus wget -O- http://api:8000/metrics`
3. Revisar logs: `docker-compose logs prometheus`

### Grafana no muestra datos
1. Verificar que Prometheus esté corriendo
2. Verificar que los datasources estén configurados correctamente
3. Revisar la configuración en Grafana > Configuration > Data Sources

### Logs no aparecen en Loki
1. Verificar que Promtail esté corriendo: `docker-compose ps promtail`
2. Verificar logs de Promtail: `docker-compose logs promtail`
3. Verificar que Loki esté accesible: `docker-compose exec promtail wget -O- http://loki:3100/ready`

## Personalización

### Agregar nuevas métricas
1. Agregar el exporter o endpoint en `prometheus/prometheus.yml`
2. Crear o actualizar el dashboard en `grafana/dashboards/`

### Agregar nuevos dashboards
1. Crear el archivo JSON en `grafana/dashboards/`
2. Los dashboards se cargarán automáticamente al reiniciar Grafana

### Modificar retención de datos
Editar `docker-compose.yml` en la sección de Prometheus:
```yaml
- '--storage.tsdb.retention.time=200h'
```

## Referencias

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [PostgreSQL Exporter](https://github.com/prometheus-community/postgres_exporter)

