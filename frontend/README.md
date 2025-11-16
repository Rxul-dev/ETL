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

## Build

```bash
npm run build
```

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

