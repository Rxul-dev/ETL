/**
 * Configuración de URLs para API y WebSocket
 * 
 * Lógica simplificada:
 * - Si VITE_API_URL está definido, usarlo
 * - Si no, usar la IP pública de la VM por defecto: http://91.98.64.119:8000
 */

// IP pública de la VM (Hetzner)
const DEFAULT_VM_IP = '91.98.64.119'
const DEFAULT_API_URL = `http://${DEFAULT_VM_IP}:8000`

/**
 * Obtiene la URL base para las peticiones HTTP (REST API)
 */
export function getApiBaseUrl(): string {
  // Si VITE_API_URL está definido y no está vacío, usarlo
  const viteApiUrl = import.meta.env.VITE_API_URL
  if (viteApiUrl && viteApiUrl.trim() !== '') {
    const url = viteApiUrl.trim()
    console.log('[API Config] Using VITE_API_URL:', url)
    return url
  }
  
  // Por defecto: usar la IP pública de la VM
  console.log('[API Config] Using default VM IP:', DEFAULT_API_URL)
  return DEFAULT_API_URL
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
  
  // Por defecto: usar la IP pública de la VM para WebSocket
  return `ws://${DEFAULT_VM_IP}:8000`
}

