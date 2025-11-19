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

La aplicación estará disponible en `http://localhost:5173`

### Configuración del Backend

**En desarrollo local:**
- El backend debe estar corriendo en `http://localhost:8000`
- Por defecto, el frontend se conecta a `http://localhost:8000`
- **Opcional**: Puedes crear un archivo `.env.local` para personalizar la URL:
  ```bash
  # frontend/.env.local
  VITE_API_URL=http://localhost:8000
  # o para usar un backend remoto:
  # VITE_API_URL=http://192.168.1.100:8000
  ```
- El archivo `.env.local` está en `.gitignore` y no se sube al repositorio

**Para producción (VM con Nginx):**
- **NO** necesitas configurar `VITE_API_URL` en producción
- El frontend usa automáticamente `/api` como base URL
- Nginx hace proxy de `/api` a `http://127.0.0.1:8000`
- Nginx también hace proxy de `/ws` para WebSocket

**Para producción personalizada (sin Nginx):**
- Configura `VITE_API_URL` en el workflow de GitHub Actions o en el build:
  ```bash
  VITE_API_URL=https://api.tudominio.com
  ```

## Build

```bash
npm run build
```

**Lógica de URLs en el build:**
- Si `VITE_API_URL` está definido → usa ese valor
- Si no está definido y es desarrollo → usa `http://localhost:8000`
- Si no está definido y es producción → usa `/api` (para Nginx proxy)

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

La configuración de URLs es automática según el entorno:

- **Desarrollo local**: 
  - API: `http://localhost:8000` (o `VITE_API_URL` de `.env.local` si existe)
  - WebSocket: `ws://localhost:8000/ws/chats/{chat_id}`

- **Producción con Nginx (VM)**:
  - API: `/api` (Nginx hace proxy a `http://127.0.0.1:8000`)
  - WebSocket: `ws://{host}/ws/chats/{chat_id}` (Nginx hace proxy)

- **Producción personalizada**:
  - API: `{VITE_API_URL}` (configurado en el build)
  - WebSocket: `ws://{host}/ws/chats/{chat_id}` (extraído de `VITE_API_URL`)

## Archivos de Configuración

- `.env.local` (opcional, para desarrollo): Define `VITE_API_URL` si necesitas una URL diferente a `http://localhost:8000`
- `.env.local.example`: Plantilla de ejemplo para `.env.local`
