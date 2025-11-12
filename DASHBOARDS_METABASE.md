# Dashboards SQL para Metabase

Este documento contiene queries SQL listas para usar en Metabase para crear dashboards visuales y llamativos del sistema ETL.

---

## 📊 Dashboard 1: Vista General del Sistema

### Métricas Principales (Cards de Números)

#### Total de Usuarios
```sql
SELECT COUNT(*) as total_usuarios
FROM dim_users;
```

#### Total de Chats
```sql
SELECT COUNT(*) as total_chats
FROM dim_chats;
```

#### Total de Mensajes
```sql
SELECT COUNT(*) as total_mensajes
FROM fact_messages;
```

#### Total de Reacciones
```sql
SELECT COUNT(*) as total_reacciones
FROM fact_reactions;
```

#### Total de Bookings
```sql
SELECT COUNT(*) as total_bookings
FROM fact_bookings;
```

#### Mensajes Promedio por Chat
```sql
SELECT 
    ROUND(AVG(msg_count), 2) as promedio_mensajes_por_chat
FROM (
    SELECT chat_id, COUNT(*) as msg_count
    FROM fact_messages
    GROUP BY chat_id
) subq;
```

---

## 📈 Dashboard 2: Actividad Temporal

### Mensajes por Día (Gráfico de Línea)
```sql
SELECT 
    created_day as fecha,
    COUNT(*) as total_mensajes
FROM fact_messages
WHERE created_day >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY created_day
ORDER BY created_day;
```

### Actividad por Hora del Día (Gráfico de Barras)
```sql
SELECT 
    created_hour as hora,
    COUNT(*) as total_mensajes
FROM fact_messages
WHERE created_day >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY created_hour
ORDER BY created_hour;
```

### Crecimiento de Usuarios (Gráfico de Línea)
```sql
SELECT 
    DATE(created_at) as fecha,
    COUNT(*) as usuarios_nuevos,
    SUM(COUNT(*)) OVER (ORDER BY DATE(created_at)) as total_acumulado
FROM dim_users
WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(created_at)
ORDER BY fecha;
```

### Mensajes y Reacciones por Día (Gráfico Dual)
```sql
SELECT 
    COALESCE(m.created_day, r.created_day) as fecha,
    COUNT(DISTINCT m.message_id) as mensajes,
    COUNT(DISTINCT r.message_id) as mensajes_con_reacciones,
    COUNT(r.message_id) as total_reacciones
FROM fact_messages m
LEFT JOIN fact_reactions r ON m.message_id = r.message_id
WHERE COALESCE(m.created_day, r.created_day) >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY COALESCE(m.created_day, r.created_day)
ORDER BY fecha;
```

---

## 👥 Dashboard 3: Análisis de Usuarios

### Top 10 Usuarios Más Activos (Tabla)
```sql
SELECT 
    u.user_id,
    u.handle,
    u.display_name,
    COUNT(DISTINCT m.message_id) as total_mensajes,
    COUNT(DISTINCT m.chat_id) as chats_participando,
    COUNT(DISTINCT r.message_id) as mensajes_con_reacciones
FROM dim_users u
LEFT JOIN fact_messages m ON u.user_id = m.sender_id
LEFT JOIN fact_reactions r ON u.user_id = r.user_id
GROUP BY u.user_id, u.handle, u.display_name
ORDER BY total_mensajes DESC
LIMIT 10;
```

### Distribución de Mensajes por Usuario (Gráfico de Barras)
```sql
SELECT 
    CASE 
        WHEN msg_count = 0 THEN '0 mensajes'
        WHEN msg_count BETWEEN 1 AND 10 THEN '1-10 mensajes'
        WHEN msg_count BETWEEN 11 AND 50 THEN '11-50 mensajes'
        WHEN msg_count BETWEEN 51 AND 100 THEN '51-100 mensajes'
        WHEN msg_count BETWEEN 101 AND 500 THEN '101-500 mensajes'
        ELSE '500+ mensajes'
    END as rango_mensajes,
    COUNT(*) as cantidad_usuarios
FROM (
    SELECT u.user_id, COUNT(m.message_id) as msg_count
    FROM dim_users u
    LEFT JOIN fact_messages m ON u.user_id = m.sender_id
    GROUP BY u.user_id
) subq
GROUP BY rango_mensajes
ORDER BY MIN(msg_count);
```

### Usuarios Nuevos por Mes (Gráfico de Barras)
```sql
SELECT 
    TO_CHAR(created_at, 'YYYY-MM') as mes,
    COUNT(*) as usuarios_nuevos
FROM dim_users
WHERE created_at >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY TO_CHAR(created_at, 'YYYY-MM')
ORDER BY mes;
```

---

## 💬 Dashboard 4: Análisis de Chats

### Top 10 Chats Más Activos (Tabla)
```sql
SELECT 
    c.chat_id,
    c.type,
    c.title,
    COUNT(DISTINCT m.message_id) as total_mensajes,
    COUNT(DISTINCT m.sender_id) as usuarios_unicos,
    COUNT(DISTINCT r.message_id) as mensajes_con_reacciones,
    MAX(m.created_at) as ultimo_mensaje
FROM dim_chats c
LEFT JOIN fact_messages m ON c.chat_id = m.chat_id
LEFT JOIN fact_reactions r ON m.message_id = r.message_id
GROUP BY c.chat_id, c.type, c.title
ORDER BY total_mensajes DESC
LIMIT 10;
```

### Distribución de Chats por Tipo (Gráfico de Pie)
```sql
SELECT 
    type as tipo_chat,
    COUNT(*) as cantidad,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM dim_chats
GROUP BY type;
```

### Mensajes Promedio por Tipo de Chat (Gráfico de Barras)
```sql
SELECT 
    c.type as tipo_chat,
    ROUND(AVG(msg_count), 2) as promedio_mensajes,
    MAX(msg_count) as max_mensajes,
    MIN(msg_count) as min_mensajes
FROM dim_chats c
LEFT JOIN (
    SELECT chat_id, COUNT(*) as msg_count
    FROM fact_messages
    GROUP BY chat_id
) m ON c.chat_id = m.chat_id
GROUP BY c.type;
```

### Chats por Tamaño (Gráfico de Barras)
```sql
SELECT 
    CASE 
        WHEN msg_count = 0 THEN '0 mensajes'
        WHEN msg_count BETWEEN 1 AND 50 THEN '1-50 mensajes'
        WHEN msg_count BETWEEN 51 AND 200 THEN '51-200 mensajes'
        WHEN msg_count BETWEEN 201 AND 500 THEN '201-500 mensajes'
        WHEN msg_count BETWEEN 501 AND 1000 THEN '501-1000 mensajes'
        ELSE '1000+ mensajes'
    END as rango_mensajes,
    COUNT(*) as cantidad_chats
FROM (
    SELECT c.chat_id, COUNT(m.message_id) as msg_count
    FROM dim_chats c
    LEFT JOIN fact_messages m ON c.chat_id = m.chat_id
    GROUP BY c.chat_id
) subq
GROUP BY rango_mensajes
ORDER BY MIN(msg_count);
```

---

## 📝 Dashboard 5: Análisis de Mensajes

### Longitud Promedio de Mensajes (Card)
```sql
SELECT 
    ROUND(AVG(message_length), 2) as longitud_promedio,
    MIN(message_length) as longitud_minima,
    MAX(message_length) as longitud_maxima
FROM fact_messages;
```

### Distribución de Longitud de Mensajes (Gráfico de Barras)
```sql
SELECT 
    CASE 
        WHEN message_length = 0 THEN '0 caracteres'
        WHEN message_length BETWEEN 1 AND 50 THEN '1-50 caracteres'
        WHEN message_length BETWEEN 51 AND 100 THEN '51-100 caracteres'
        WHEN message_length BETWEEN 101 AND 200 THEN '101-200 caracteres'
        WHEN message_length BETWEEN 201 AND 500 THEN '201-500 caracteres'
        ELSE '500+ caracteres'
    END as rango_longitud,
    COUNT(*) as cantidad_mensajes,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM fact_messages
GROUP BY rango_longitud
ORDER BY MIN(message_length);
```

### Mensajes con Respuestas (Card)
```sql
SELECT 
    COUNT(*) FILTER (WHERE reply_to_id IS NOT NULL) as mensajes_con_respuesta,
    COUNT(*) FILTER (WHERE reply_to_id IS NULL) as mensajes_sin_respuesta,
    ROUND(100.0 * COUNT(*) FILTER (WHERE reply_to_id IS NOT NULL) / COUNT(*), 2) as porcentaje_con_respuesta
FROM fact_messages;
```

### Mensajes Editados (Card)
```sql
SELECT 
    COUNT(*) FILTER (WHERE edited_at IS NOT NULL) as mensajes_editados,
    COUNT(*) as total_mensajes,
    ROUND(100.0 * COUNT(*) FILTER (WHERE edited_at IS NOT NULL) / COUNT(*), 2) as porcentaje_editados
FROM fact_messages;
```

### Top 20 Mensajes Más Largos (Tabla)
```sql
SELECT 
    m.message_id,
    m.chat_id,
    c.title as chat_title,
    u.handle as sender,
    m.message_length,
    LEFT(m.body, 100) as preview
FROM fact_messages m
LEFT JOIN dim_chats c ON m.chat_id = c.chat_id
LEFT JOIN dim_users u ON m.sender_id = u.user_id
ORDER BY m.message_length DESC
LIMIT 20;
```

---

## ⚡ Dashboard 6: Análisis de Reacciones

### Emojis Más Usados (Gráfico de Barras)
```sql
SELECT 
    emoji,
    COUNT(*) as total_usos,
    COUNT(DISTINCT message_id) as mensajes_unicos,
    COUNT(DISTINCT user_id) as usuarios_unicos
FROM fact_reactions
GROUP BY emoji
ORDER BY total_usos DESC
LIMIT 20;
```

### Mensajes Más Reaccionados (Tabla)
```sql
SELECT 
    m.message_id,
    m.chat_id,
    c.title as chat_title,
    u.handle as sender,
    LEFT(m.body, 80) as preview,
    COUNT(DISTINCT r.user_id) as usuarios_reaccionando,
    COUNT(r.emoji) as total_reacciones,
    COUNT(DISTINCT r.emoji) as emojis_unicos
FROM fact_messages m
LEFT JOIN fact_reactions r ON m.message_id = r.message_id
LEFT JOIN dim_chats c ON m.chat_id = c.chat_id
LEFT JOIN dim_users u ON m.sender_id = u.user_id
GROUP BY m.message_id, m.chat_id, c.title, u.handle, m.body
HAVING COUNT(r.emoji) > 0
ORDER BY total_reacciones DESC
LIMIT 20;
```

### Tasa de Reacciones (Card)
```sql
SELECT 
    COUNT(DISTINCT m.message_id) as total_mensajes,
    COUNT(DISTINCT r.message_id) as mensajes_con_reacciones,
    ROUND(100.0 * COUNT(DISTINCT r.message_id) / COUNT(DISTINCT m.message_id), 2) as porcentaje_con_reacciones,
    ROUND(COUNT(r.emoji)::numeric / COUNT(DISTINCT m.message_id), 2) as reacciones_por_mensaje
FROM fact_messages m
LEFT JOIN fact_reactions r ON m.message_id = r.message_id;
```

### Reacciones por Día (Gráfico de Línea)
```sql
SELECT 
    created_day as fecha,
    COUNT(*) as total_reacciones,
    COUNT(DISTINCT message_id) as mensajes_reaccionados,
    COUNT(DISTINCT user_id) as usuarios_reaccionando
FROM fact_reactions
WHERE created_day >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY created_day
ORDER BY fecha;
```

---

## 📅 Dashboard 7: Análisis de Bookings

### Bookings por Estado (Gráfico de Pie)
```sql
SELECT 
    status as estado,
    COUNT(*) as cantidad,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM fact_bookings
GROUP BY status
ORDER BY cantidad DESC;
```

### Bookings por Tipo (Gráfico de Barras)
```sql
SELECT 
    COALESCE(booking_type, 'Sin tipo') as tipo_booking,
    COUNT(*) as cantidad,
    COUNT(*) FILTER (WHERE status = 'CONFIRMED') as confirmados,
    COUNT(*) FILTER (WHERE status = 'PENDING') as pendientes,
    COUNT(*) FILTER (WHERE status = 'CANCELLED') as cancelados
FROM fact_bookings
GROUP BY booking_type
ORDER BY cantidad DESC;
```

### Bookings por Día (Gráfico de Línea)
```sql
SELECT 
    created_day as fecha,
    COUNT(*) as total_bookings,
    COUNT(*) FILTER (WHERE status = 'CONFIRMED') as confirmados,
    COUNT(*) FILTER (WHERE status = 'PENDING') as pendientes
FROM fact_bookings
WHERE created_day >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY created_day
ORDER BY fecha;
```

### Top Usuarios con Más Bookings (Tabla)
```sql
SELECT 
    u.user_id,
    u.handle,
    u.display_name,
    COUNT(b.booking_id) as total_bookings,
    COUNT(*) FILTER (WHERE b.status = 'CONFIRMED') as confirmados,
    COUNT(*) FILTER (WHERE b.status = 'PENDING') as pendientes
FROM dim_users u
JOIN fact_bookings b ON u.user_id = b.user_id
GROUP BY u.user_id, u.handle, u.display_name
ORDER BY total_bookings DESC
LIMIT 10;
```

### Eventos de Bookings por Tipo (Gráfico de Barras)
```sql
SELECT 
    event_type as tipo_evento,
    COUNT(*) as cantidad,
    COUNT(DISTINCT booking_id) as bookings_unicos
FROM fact_booking_events
GROUP BY event_type
ORDER BY cantidad DESC;
```

---

## 🔥 Dashboard 8: Métricas de Engagement

### Tasa de Participación por Chat (Tabla)
```sql
SELECT 
    c.chat_id,
    c.title,
    c.type,
    COUNT(DISTINCT bcm.user_id) as total_miembros,
    COUNT(DISTINCT m.sender_id) as miembros_activos,
    COUNT(m.message_id) as total_mensajes,
    ROUND(100.0 * COUNT(DISTINCT m.sender_id) / COUNT(DISTINCT bcm.user_id), 2) as tasa_participacion,
    ROUND(COUNT(m.message_id)::numeric / NULLIF(COUNT(DISTINCT bcm.user_id), 0), 2) as mensajes_por_miembro
FROM dim_chats c
LEFT JOIN bridge_chat_members bcm ON c.chat_id = bcm.chat_id
LEFT JOIN fact_messages m ON c.chat_id = m.chat_id
GROUP BY c.chat_id, c.title, c.type
HAVING COUNT(DISTINCT bcm.user_id) > 0
ORDER BY tasa_participacion DESC
LIMIT 20;
```

### Engagement Score por Usuario (Tabla)
```sql
SELECT 
    u.user_id,
    u.handle,
    u.display_name,
    COUNT(DISTINCT m.message_id) as mensajes_enviados,
    COUNT(DISTINCT r.message_id) as reacciones_dadas,
    COUNT(DISTINCT m.chat_id) as chats_participando,
    COUNT(DISTINCT b.booking_id) as bookings_realizados,
    (COUNT(DISTINCT m.message_id) * 1 + 
     COUNT(DISTINCT r.message_id) * 0.5 + 
     COUNT(DISTINCT m.chat_id) * 2 + 
     COUNT(DISTINCT b.booking_id) * 3) as engagement_score
FROM dim_users u
LEFT JOIN fact_messages m ON u.user_id = m.sender_id
LEFT JOIN fact_reactions r ON u.user_id = r.user_id
LEFT JOIN fact_bookings b ON u.user_id = b.user_id
GROUP BY u.user_id, u.handle, u.display_name
HAVING (COUNT(DISTINCT m.message_id) + COUNT(DISTINCT r.message_id)) > 0
ORDER BY engagement_score DESC
LIMIT 20;
```

---

## 📊 Dashboard 9: Tendencias y Comparativas

### Comparativa Semanal (Gráfico de Línea)
```sql
SELECT 
    DATE_TRUNC('week', created_day) as semana,
    COUNT(DISTINCT m.message_id) as mensajes,
    COUNT(DISTINCT r.message_id) as reacciones,
    COUNT(DISTINCT b.booking_id) as bookings
FROM fact_messages m
FULL OUTER JOIN fact_reactions r ON DATE_TRUNC('week', m.created_day) = DATE_TRUNC('week', r.created_day)
FULL OUTER JOIN fact_bookings b ON DATE_TRUNC('week', m.created_day) = DATE_TRUNC('week', b.created_day)
WHERE COALESCE(m.created_day, r.created_day, b.created_day) >= CURRENT_DATE - INTERVAL '12 weeks'
GROUP BY DATE_TRUNC('week', COALESCE(m.created_day, r.created_day, b.created_day))
ORDER BY semana;
```

### Actividad por Día de la Semana (Gráfico de Barras)
```sql
SELECT 
    TO_CHAR(created_day, 'Day') as dia_semana,
    EXTRACT(DOW FROM created_day) as dia_numero,
    COUNT(*) as total_mensajes,
    ROUND(AVG(COUNT(*)) OVER (), 2) as promedio
FROM fact_messages
WHERE created_day >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY TO_CHAR(created_day, 'Day'), EXTRACT(DOW FROM created_day)
ORDER BY dia_numero;
```

### Comparativa: Chats Individuales vs Grupales (Gráfico de Barras Agrupadas)
```sql
SELECT 
    type as tipo_chat,
    COUNT(DISTINCT c.chat_id) as total_chats,
    COUNT(DISTINCT m.message_id) as total_mensajes,
    COUNT(DISTINCT bcm.user_id) as total_miembros,
    ROUND(COUNT(DISTINCT m.message_id)::numeric / NULLIF(COUNT(DISTINCT c.chat_id), 0), 2) as mensajes_por_chat,
    ROUND(COUNT(DISTINCT m.message_id)::numeric / NULLIF(COUNT(DISTINCT bcm.user_id), 0), 2) as mensajes_por_miembro
FROM dim_chats c
LEFT JOIN fact_messages m ON c.chat_id = m.chat_id
LEFT JOIN bridge_chat_members bcm ON c.chat_id = bcm.chat_id
GROUP BY type;
```

---

## 🎯 Dashboard 10: Métricas de Calidad

### Mensajes sin Sender (Card - Alerta)
```sql
SELECT 
    COUNT(*) as mensajes_sin_sender,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_messages), 2) as porcentaje
FROM fact_messages
WHERE sender_id IS NULL;
```

### Chats sin Mensajes (Card - Alerta)
```sql
SELECT 
    COUNT(*) as chats_sin_mensajes
FROM dim_chats c
LEFT JOIN fact_messages m ON c.chat_id = m.chat_id
WHERE m.message_id IS NULL;
```

### Usuarios Inactivos (Card)
```sql
SELECT 
    COUNT(*) as usuarios_inactivos
FROM dim_users u
LEFT JOIN fact_messages m ON u.user_id = m.sender_id
LEFT JOIN fact_reactions r ON u.user_id = r.user_id
WHERE m.message_id IS NULL AND r.message_id IS NULL;
```

### Integridad Referencial (Card)
```sql
SELECT 
    COUNT(*) FILTER (WHERE m.chat_id NOT IN (SELECT chat_id FROM dim_chats)) as mensajes_chat_huérfano,
    COUNT(*) FILTER (WHERE m.sender_id IS NOT NULL AND m.sender_id NOT IN (SELECT user_id FROM dim_users)) as mensajes_sender_huérfano,
    COUNT(*) FILTER (WHERE r.message_id NOT IN (SELECT message_id FROM fact_messages)) as reacciones_mensaje_huérfano
FROM fact_messages m
FULL OUTER JOIN fact_reactions r ON TRUE;
```

---

## 📈 Dashboard 11: Análisis Avanzado

### Velocidad de Respuesta (Tabla)
```sql
SELECT 
    m1.message_id,
    m1.chat_id,
    u1.handle as remitente,
    m2.message_id as respuesta_a,
    u2.handle as respondido_por,
    EXTRACT(EPOCH FROM (m2.created_at - m1.created_at)) / 60 as minutos_para_responder
FROM fact_messages m1
JOIN fact_messages m2 ON m2.reply_to_id = m1.message_id
LEFT JOIN dim_users u1 ON m1.sender_id = u1.user_id
LEFT JOIN dim_users u2 ON m2.sender_id = u2.user_id
WHERE m2.created_at - m1.created_at < INTERVAL '7 days'
ORDER BY minutos_para_responder
LIMIT 50;
```

### Tiempo Promedio de Respuesta (Card)
```sql
SELECT 
    ROUND(AVG(EXTRACT(EPOCH FROM (m2.created_at - m1.created_at)) / 60), 2) as minutos_promedio,
    ROUND(AVG(EXTRACT(EPOCH FROM (m2.created_at - m1.created_at)) / 3600), 2) as horas_promedio
FROM fact_messages m1
JOIN fact_messages m2 ON m2.reply_to_id = m1.message_id
WHERE m2.created_at - m1.created_at < INTERVAL '7 days';
```

### Chats con Mayor Actividad Reciente (Tabla)
```sql
SELECT 
    c.chat_id,
    c.title,
    c.type,
    COUNT(m.message_id) as mensajes_ultimos_7_dias,
    MAX(m.created_at) as ultimo_mensaje,
    COUNT(DISTINCT m.sender_id) as usuarios_activos
FROM dim_chats c
JOIN fact_messages m ON c.chat_id = m.chat_id
WHERE m.created_day >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY c.chat_id, c.title, c.type
ORDER BY mensajes_ultimos_7_dias DESC
LIMIT 20;
```

---

## 🎨 Recomendaciones de Visualización en Metabase

### Para Gráficos de Línea:
- **Color**: Azul (#4A90E2) para mensajes, Verde (#50C878) para reacciones, Naranja (#FF6B35) para bookings
- **Mostrar puntos**: Sí, para destacar valores
- **Suavizar líneas**: Opcional, para tendencias más claras

### Para Gráficos de Barras:
- **Orientación**: Horizontal para top 10/20, Vertical para comparativas
- **Colores**: Gradiente o colores distintos por categoría
- **Mostrar valores**: Sí, en las barras

### Para Gráficos de Pie:
- **Mostrar porcentajes**: Sí
- **Límite de categorías**: Máximo 8-10, agrupar el resto en "Otros"

### Para Tablas:
- **Paginación**: 20-50 filas por página
- **Ordenamiento**: Por defecto por la métrica principal
- **Formato de números**: Con separadores de miles

### Cards de Números:
- **Formato**: Con separadores (1,234)
- **Iconos**: Usuarios 👥, Mensajes 💬, Reacciones ⚡, Bookings 📅
- **Comparación**: Mostrar cambio vs período anterior si es posible

---

## 🚀 Cómo Usar en Metabase

1. **Crear una Nueva Pregunta**:
   - Click en "New" → "Question"
   - Selecciona "Native Query"
   - Pega una de las queries SQL
   - Click en "Visualize"

2. **Configurar Visualización**:
   - Selecciona el tipo de gráfico apropiado
   - Ajusta colores y formato según recomendaciones

3. **Crear Dashboard**:
   - Click en "New" → "Dashboard"
   - Arrastra las preguntas creadas
   - Organiza en secciones lógicas

4. **Agregar Filtros** (Opcional):
   - Filtros de fecha para análisis temporales
   - Filtros de chat_id o user_id para análisis específicos

---

## 📝 Notas Importantes

- Todas las queries asumen que las tablas existen y tienen datos
- Ajusta los intervalos de tiempo según tus necesidades
- Los límites (LIMIT) pueden ajustarse según el volumen de datos
- Considera agregar índices adicionales si las queries son lentas
- Para datos históricos muy grandes, considera usar particionamiento

---

## 🔧 Queries de Optimización

Si alguna query es lenta, puedes optimizarla agregando estas condiciones:

```sql
-- Agregar índice si no existe
CREATE INDEX IF NOT EXISTS idx_fact_messages_created_day 
  ON fact_messages(created_day);

CREATE INDEX IF NOT EXISTS idx_fact_reactions_created_day 
  ON fact_reactions(created_day);

CREATE INDEX IF NOT EXISTS idx_fact_bookings_created_day 
  ON fact_bookings(created_day);
```

