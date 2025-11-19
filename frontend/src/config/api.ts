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
  // Si VITE_API_URL está definido y no está vacío, usarlo
  // (útil para desarrollo con .env.local o producción personalizada)
  const viteApiUrl = import.meta.env.VITE_API_URL
  if (viteApiUrl && viteApiUrl.trim() !== '') {
    const url = viteApiUrl.trim()
    if (import.meta.env.DEV) {
      console.log('[API Config] Using VITE_API_URL from .env.local:', url)
    }
    return url
  }
  
  // En desarrollo: usar localhost:8000
  if (import.meta.env.DEV) {
    console.log('[API Config] Development mode: using http://localhost:8000')
    return 'http://localhost:8000'
  }
  
  // En producción: usar /api (Nginx hace proxy)
  console.log('[API Config] Production mode: using /api (Nginx proxy)')
  return '/api'
}

/**
 * Obtiene la URL base para WebSocket
 */
export function getWebSocketBaseUrl(): string {
  // Si VITE_API_URL está definido y no está vacío, extraer el host y protocolo
  const viteApiUrl = import.meta.env.VITE_API_URL
  if (viteApiUrl && viteApiUrl.trim() !== '') {
    try {
      const url = new URL(viteApiUrl.trim())
      const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
      return `${protocol}//${url.host}`
    } catch {
      // Si no es una URL válida, intentar convertir http/https a ws/wss
      const trimmed = viteApiUrl.trim()
      return trimmed.replace(/^https:\/\//, 'wss://').replace(/^http:\/\//, 'ws://')
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

