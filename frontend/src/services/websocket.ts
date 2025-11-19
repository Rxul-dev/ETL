import { Message } from '../api/client'

export interface WebSocketMessage {
  type: 'connection' | 'new_message' | 'pong'
  status?: string
  chat_id?: number
  message?: Message
}

export class WebSocketService {
  private ws: WebSocket | null = null
  public chatId: number | null = null
  private userId: number | null = null
  private onMessageCallback: ((message: Message) => void) | null = null
  private onErrorCallback: ((error: Event) => void) | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private isIntentionallyDisconnected = false
  private connectionTimeout: NodeJS.Timeout | null = null

  connect(chatId: number, userId?: number): Promise<void> {
    return new Promise((resolve, reject) => {
      // Limpiar conexión anterior si existe
      if (this.ws) {
        // Marcar como desconexión intencional para evitar reconexión
        this.isIntentionallyDisconnected = true
        try {
          if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
            this.ws.close()
          }
        } catch (error) {
          // Ignorar errores al cerrar conexión anterior
        }
        this.ws = null
      }

      this.chatId = chatId
      this.userId = userId || null
      this.isIntentionallyDisconnected = false

      const wsUrl = `ws://localhost:8000/ws/chats/${chatId}${userId ? `?user_id=${userId}` : ''}`
      this.ws = new WebSocket(wsUrl)

      // Timeout para la conexión
      this.connectionTimeout = setTimeout(() => {
        if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
          console.error('WebSocket connection timeout')
          this.ws.close()
          reject(new Error('Connection timeout'))
        }
      }, 10000) // 10 segundos de timeout

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
        if (this.connectionTimeout) {
          clearTimeout(this.connectionTimeout)
          this.connectionTimeout = null
        }
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data)
          
          if (data.type === 'new_message' && data.message) {
            if (this.onMessageCallback) {
              this.onMessageCallback(data.message)
            }
          } else if (data.type === 'connection') {
            console.log('WebSocket connection confirmed:', data)
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        // Solo registrar errores si la conexión no se ha establecido
        if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
          console.warn('WebSocket error during connection:', error)
          if (this.onErrorCallback) {
            this.onErrorCallback(error)
          }
        }
        // No rechazar la promesa aquí, esperar a ver si se conecta
      }

      this.ws.onclose = (event) => {
        if (this.connectionTimeout) {
          clearTimeout(this.connectionTimeout)
          this.connectionTimeout = null
        }

        // Solo intentar reconectar si no fue una desconexión intencional
        // y el código de cierre no es 1000 (cierre normal)
        if (!this.isIntentionallyDisconnected && event.code !== 1000 && event.code !== 1001) {
          console.log('WebSocket closed unexpectedly, attempting to reconnect...')
          this.attemptReconnect()
        } else {
          // No registrar como error si fue intencional o cierre normal
          if (!this.isIntentionallyDisconnected) {
            console.log('WebSocket closed')
          }
        }
      }
    })
  }

  private attemptReconnect() {
    if (this.isIntentionallyDisconnected) {
      return // No reconectar si fue una desconexión intencional
    }
    
    if (this.reconnectAttempts < this.maxReconnectAttempts && this.chatId) {
      this.reconnectAttempts++
      setTimeout(() => {
        if (!this.isIntentionallyDisconnected && this.chatId) {
          console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
          this.connect(this.chatId!, this.userId || undefined).catch((error) => {
            console.error('Reconnection failed:', error)
          })
        }
      }, this.reconnectDelay * this.reconnectAttempts)
    } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      if (this.onErrorCallback) {
        this.onErrorCallback(new Event('max_reconnect_attempts'))
      }
    }
  }

  disconnect() {
    this.isIntentionallyDisconnected = true
    
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout)
      this.connectionTimeout = null
    }
    
    if (this.ws) {
      // Solo cerrar si la conexión está abierta
      // CONNECTING = 0, OPEN = 1, CLOSING = 2, CLOSED = 3
      try {
        if (this.ws.readyState === WebSocket.OPEN) {
          this.ws.close(1000, 'Intentional disconnect')
        } else if (this.ws.readyState === WebSocket.CONNECTING) {
          // Si está conectando, simplemente limpiar la referencia
          // El WebSocket se cerrará automáticamente cuando se desmonte
          // No intentar cerrar explícitamente para evitar el error
        }
      } catch (error) {
        // Ignorar errores al cerrar, solo limpiar la referencia
        // Esto puede ocurrir si el WebSocket ya está cerrado
      }
      this.ws = null
    }
    
    this.chatId = null
    this.userId = null
    this.reconnectAttempts = 0
  }

  onMessage(callback: (message: Message) => void) {
    this.onMessageCallback = callback
  }

  onError(callback: (error: Event) => void) {
    this.onErrorCallback = callback
  }

  sendPing() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'ping' }))
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}

