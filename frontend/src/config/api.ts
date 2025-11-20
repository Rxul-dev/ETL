

// IP pública de la VM (Hetzner)
const DEFAULT_VM_IP = '91.98.64.119'
const DEFAULT_API_URL = `http://${DEFAULT_VM_IP}:8000`
// const DEFAULT_API_URL = `http://localhost:8000` //cambiar luego

export function getApiBaseUrl(): string {
  const viteApiUrl = import.meta.env.VITE_API_URL
  if (viteApiUrl && viteApiUrl.trim() !== '') {
    const url = viteApiUrl.trim()
    console.log('[API Config] Using VITE_API_URL:', url)
    return url
  }
  
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
  
  return `ws://${DEFAULT_VM_IP}:8000` 
}

