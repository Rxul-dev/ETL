import { Message } from '../api/client'
import { getWebSocketBaseUrl } from '../config/api'

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

  connect(chatId: number, userId?: number): Promise<void> {
    return new Promise((resolve, reject) => {
      // Si ya hay una conexión para este chat, no crear otra
      if (this.ws && this.chatId === chatId && this.ws.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      if (this.ws) {
        this.isIntentionallyDisconnected = true
        this.ws.close()
        this.ws = null
      }

      this.chatId = chatId
      this.userId = userId || null
      this.isIntentionallyDisconnected = false

      // Obtener la URL base del WebSocket según el entorno
      const wsBaseUrl = getWebSocketBaseUrl()
      const wsUrl = `${wsBaseUrl}/ws/chats/${chatId}${userId ? `?user_id=${userId}` : ''}`
      
      try {
        this.ws = new WebSocket(wsUrl)
      } catch (error) {
        reject(error)
        return
      }

      // Timeout para la conexión inicial
      const connectionTimeout = setTimeout(() => {
        if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
          this.ws.close()
          reject(new Error('WebSocket connection timeout'))
        }
      }, 10000) // 10 segundos

      this.ws.onopen = () => {
        clearTimeout(connectionTimeout)
        this.reconnectAttempts = 0
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
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        clearTimeout(connectionTimeout)
        // Solo loggear errores durante la conexión si no es una desconexión intencional
        if (!this.isIntentionallyDisconnected) {
          if (this.ws?.readyState === WebSocket.CONNECTING) {
            // Error durante la conexión inicial
            console.warn('WebSocket connection error (may be intentional):', error)
          } else {
            // Error después de conectado
            console.error('WebSocket error:', error)
          }
        }
        if (this.onErrorCallback && !this.isIntentionallyDisconnected) {
          this.onErrorCallback(error)
        }
      }

      this.ws.onclose = (event) => {
        if (!this.isIntentionallyDisconnected && event.code !== 1000 && event.code !== 1001) {
          this.attemptReconnect()
        } else {
          // Resetear la bandera después de un cierre intencional
          this.isIntentionallyDisconnected = false
        }
      }
    })
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts && this.chatId) {
      this.reconnectAttempts++
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
        this.connect(this.chatId!, this.userId || undefined).catch(console.error)
      }, this.reconnectDelay * this.reconnectAttempts)
    }
  }

  disconnect() {
    this.isIntentionallyDisconnected = true
    
    if (this.ws) {
      try {
        if (this.ws.readyState === WebSocket.OPEN) {
          this.ws.close(1000, 'Intentional disconnect')
        } else if (this.ws.readyState === WebSocket.CONNECTING) {
        }
      } catch (error) {
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

