# Palabras Clave para Creación Automática de Bookings

Este documento lista todas las palabras clave que activan la creación automática de bookings cuando se incluyen en un mensaje.

## Palabras Clave

### Reservas
- `reservar`
- `reserva`
- `reservación`
- `reservacion`

### Booking (en inglés)
- `booking`
- `book`

### Agendamiento
- `agendar`
- `agenda`
- `agendamiento`

### Citas
- `cita`
- `citas`

### Frases Completas
- `reservar sala`
- `reservar habitación`
- `reservar cuarto`
- `sala disponible`
- `habitación disponible`
- `necesito sala`
- `necesito habitación`

### Disponibilidad
- `disponible`
- `disponibilidad`

## Cómo Funciona

Cuando envías un mensaje que contiene cualquiera de estas palabras clave (sin importar mayúsculas o minúsculas), el sistema automáticamente:

1. Detecta la palabra clave en el mensaje
2. Espera 500ms para que el mensaje se guarde en la base de datos
3. Crea un booking asociado al mensaje
4. Muestra una notificación: "✅ Booking creado automáticamente"

## Ejemplos

### ✅ Se creará un booking:
- "Quiero **reservar** una sala"
- "Necesito hacer un **booking** para mañana"
- "¿Hay alguna **habitación disponible**?"
- "Quiero **agendar** una cita"
- "Necesito **reservar** para el viernes"

### ❌ No se creará un booking:
- "Hola, ¿cómo estás?"
- "Gracias por la información"
- "Nos vemos mañana"

## Notas

- La detección es **case-insensitive** (no distingue entre mayúsculas y minúsculas)
- La palabra clave puede aparecer en cualquier parte del mensaje
- Solo se crea un booking por mensaje
- El booking se crea con tipo "room" por defecto
- La fecha del booking es opcional y se puede especificar después

