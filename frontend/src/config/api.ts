/**
 * Configuración de URLs para API y WebSocket
 * 
 * Lógica:
 * - En desarrollo: usa VITE_API_URL de .env.local si existe, si no http://localhost:8000
 * - En producción: usa /api si no hay VITE_API_URL (Nginx hace proxy a http://127.0.0.1:8000)
 */

/**
 * Obtiene la URL base para las peticiones HTTP (REST API)
 */
export function getApiBaseUrl(): string {
  // Si VITE_API_URL está definido, usarlo (útil para desarrollo con .env.local o producción personalizada)
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  
  // En desarrollo: usar localhost:8000
  if (import.meta.env.DEV) {
    return 'http://localhost:8000'
  }
  
  // En producción: usar /api (Nginx hace proxy)
  return '/api'
}

/**
 * Obtiene la URL base para WebSocket
 */
export function getWebSocketBaseUrl(): string {
  // Si VITE_API_URL está definido, extraer el host y protocolo
  if (import.meta.env.VITE_API_URL) {
    try {
      const url = new URL(import.meta.env.VITE_API_URL)
      const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
      return `${protocol}//${url.host}`
    } catch {
      // Si no es una URL válida, usar el valor tal cual
      return import.meta.env.VITE_API_URL.replace(/^https?:\/\//, 'ws://').replace(/^http:\/\//, 'ws://')
    }
  }
  
  // En desarrollo: usar ws://localhost:8000
  if (import.meta.env.DEV) {
    return 'ws://localhost:8000'
  }
  
  // En producción: usar el mismo host que la página (Nginx hace proxy de /ws)
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}`
}

