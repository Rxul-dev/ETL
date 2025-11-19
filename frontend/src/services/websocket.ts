import { Message } from '../api/client'

export interface WebSocketMessage {
  type: 'connection' | 'new_message' | 'pong'
  status?: string
  chat_id?: number
  message?: Message
}

export class WebSocketService {
  private ws: WebSocket | null = null
  private chatId: number | null = null
  private userId: number | null = null
  private onMessageCallback: ((message: Message) => void) | null = null
  private onErrorCallback: ((error: Event) => void) | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  connect(chatId: number, userId?: number): Promise<void> {
    return new Promise((resolve, reject) => {
      this.chatId = chatId
      this.userId = userId || null

      // Construir URL del WebSocket dinámicamente
      // En desarrollo: ws://localhost:8000/ws/...
      // En producción: ws://host/ws/... (nginx proxy)
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = import.meta.env.DEV 
        ? 'localhost:8000' 
        : window.location.host
      const wsUrl = `${protocol}//${host}/ws/chats/${chatId}${userId ? `?user_id=${userId}` : ''}`
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
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
            console.log('WebSocket connection confirmed:', data)
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        if (this.onErrorCallback) {
          this.onErrorCallback(error)
        }
        reject(error)
      }

      this.ws.onclose = () => {
        console.log('WebSocket closed')
        this.attemptReconnect()
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
    if (this.ws) {
      this.ws.close()
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

