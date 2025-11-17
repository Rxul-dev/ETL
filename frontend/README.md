# Rxul Chat Frontend

Aplicación web frontend para el sistema de mensajería Rxul Chat.

## Tecnologías

- React 18
- TypeScript
- Vite
- React Router
- Zustand (state management)
- Axios (HTTP client)
- Vitest (testing)

## Instalación

```bash
npm install
```

## Desarrollo

```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:3000`

### Configuración del Backend

**En desarrollo local:**
- El backend debe estar corriendo en `http://localhost:8000`
- El proxy de Vite está configurado automáticamente
- No necesitas configurar `VITE_API_URL` en desarrollo

**Para producción:**
- Crea un archivo `.env` basado en `.env.example`
- Configura `VITE_API_URL` con la URL de tu servidor:
  ```bash
  VITE_API_URL=https://api.tudominio.com
  # o
  VITE_API_URL=http://tu-servidor-hetzner:8000
  ```

## Build

```bash
npm run build
```

El build usará la variable `VITE_API_URL` si está configurada, o `http://localhost:8000` por defecto.

## Testing

```bash
npm test
npm run test:coverage
```

## Estructura

- `src/pages/` - Páginas principales (Login, ChatList, ChatRoom)
- `src/components/` - Componentes reutilizables
- `src/api/` - Cliente API y tipos
- `src/services/` - Servicios (WebSocket)
- `src/store/` - Estado global (Zustand)
- `src/test/` - Configuración de tests

## URLs del Backend

- **Desarrollo local**: `http://localhost:8000`
- **Docker Compose**: `http://localhost:8000` (puerto expuesto)
- **Producción**: Configurar según tu servidor (Hetzner, etc.)

## WebSocket

El WebSocket se conecta automáticamente a:
- **Desarrollo**: `ws://localhost:8000/ws/chats/{chat_id}`
- **Producción**: `ws://{VITE_API_URL}/ws/chats/{chat_id}` (reemplazando `http://` por `ws://`)
