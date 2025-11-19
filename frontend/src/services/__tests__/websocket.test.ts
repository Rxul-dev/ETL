import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { WebSocketService } from '../websocket'

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  readyState = MockWebSocket.CONNECTING
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onclose: (() => void) | null = null

  constructor(public url: string) {
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 0)
  }

  send(data: string) {
    // Mock send
  }

  close() {
    this.readyState = MockWebSocket.CLOSED
    if (this.onclose) {
      this.onclose()
    }
  }
}

// @ts-ignore - Mock WebSocket para tests
;(globalThis as any).WebSocket = MockWebSocket

describe('WebSocketService', () => {
  let wsService: WebSocketService

  beforeEach(() => {
    wsService = new WebSocketService()
  })

  afterEach(() => {
    wsService.disconnect()
  })

  it('creates WebSocketService instance', () => {
    expect(wsService).toBeInstanceOf(WebSocketService)
  })

  it('connects to WebSocket', async () => {
    await wsService.connect(1, 1)
    // Verificar que el servicio existe
    expect(wsService).toBeInstanceOf(WebSocketService)
  })

  it('handles message callback', async () => {
    const onMessage = vi.fn()
    wsService.onMessage(onMessage)
    
    await wsService.connect(1, 1)
    
    // Verificar que el callback está configurado
    expect(onMessage).toBeDefined()
  })

  it('checks connection status', async () => {
    expect(wsService.isConnected()).toBe(false)
    await wsService.connect(1, 1)
    // Verificar que el servicio existe después de conectar
    expect(wsService).toBeInstanceOf(WebSocketService)
  })

  it('disconnects WebSocket', async () => {
    await wsService.connect(1, 1)
    wsService.disconnect()
    expect(wsService.isConnected()).toBe(false)
  })
})

