import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock axios antes de cualquier importación
const mockPost = vi.fn()
const mockGet = vi.fn()

vi.mock('axios', () => {
  return {
    default: {
      create: vi.fn(() => ({
        post: mockPost,
        get: mockGet,
      })),
    },
  }
})

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset modules para re-importar con el mock
    vi.resetModules()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('creates user', async () => {
    const { usersApi } = await import('../client')
    const mockUser = { id: 1, handle: 'test', display_name: 'Test', created_at: new Date().toISOString() }
    mockPost.mockResolvedValue({ data: mockUser })
    
    const result = await usersApi.create('test', 'Test')
    expect(result).toEqual(mockUser)
    expect(mockPost).toHaveBeenCalledWith('/users', { handle: 'test', display_name: 'Test' })
  })

  it('gets user by id', async () => {
    const { usersApi } = await import('../client')
    const mockUser = { id: 1, handle: 'test', display_name: 'Test', created_at: new Date().toISOString() }
    mockGet.mockResolvedValue({ data: mockUser })
    
    const result = await usersApi.get(1)
    expect(result).toEqual(mockUser)
    expect(mockGet).toHaveBeenCalledWith('/users/1')
  })

  it('lists users', async () => {
    const { usersApi } = await import('../client')
    const mockResponse = {
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    }
    mockGet.mockResolvedValue({ data: mockResponse })
    
    const result = await usersApi.list(1, 50)
    expect(result).toEqual(mockResponse)
  })

  it('creates chat', async () => {
    const { chatsApi } = await import('../client')
    const mockChat = { id: 1, type: 'group' as const, title: 'Test Chat', created_at: new Date().toISOString() }
    mockPost.mockResolvedValue({ data: mockChat })
    
    const result = await chatsApi.create('group', 'Test Chat', [1])
    expect(result).toEqual(mockChat)
  })

  it('gets chat by id', async () => {
    const { chatsApi } = await import('../client')
    const mockChat = { id: 1, type: 'group' as const, title: 'Test Chat', created_at: new Date().toISOString() }
    mockGet.mockResolvedValue({ data: mockChat })
    
    const result = await chatsApi.get(1)
    expect(result).toEqual(mockChat)
  })

  it('sends message', async () => {
    const { messagesApi } = await import('../client')
    const mockMessage = {
      id: 1,
      chat_id: 1,
      sender_id: 1,
      body: 'Test message',
      created_at: new Date().toISOString(),
      edited_at: null,
      reply_to_id: null,
    }
    mockPost.mockResolvedValue({ data: mockMessage })
    
    const result = await messagesApi.send(1, 'Test message', 1)
    expect(result).toEqual(mockMessage)
  })

  it('lists messages', async () => {
    const { messagesApi } = await import('../client')
    const mockResponse = {
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    }
    mockGet.mockResolvedValue({ data: mockResponse })
    
    const result = await messagesApi.list(1, 1, 50)
    expect(result).toEqual(mockResponse)
  })
})
