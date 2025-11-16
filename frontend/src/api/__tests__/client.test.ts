import { describe, it, expect, vi, beforeEach } from 'vitest'
import { usersApi, chatsApi, messagesApi } from '../client'
import axios from 'axios'

vi.mock('axios')
const mockedAxios = vi.mocked(axios)

describe('API Client', () => {
  beforeEach(() => {
    mockedAxios.create.mockReturnValue(mockedAxios)
  })

  describe('usersApi', () => {
    it('creates user', async () => {
      const mockUser = { id: 1, handle: 'test', display_name: 'Test', created_at: new Date().toISOString() }
      mockedAxios.post.mockResolvedValue({ data: mockUser })

      const result = await usersApi.create('test', 'Test')
      expect(result).toEqual(mockUser)
      expect(mockedAxios.post).toHaveBeenCalledWith('/users', { handle: 'test', display_name: 'Test' })
    })

    it('gets user by id', async () => {
      const mockUser = { id: 1, handle: 'test', display_name: 'Test', created_at: new Date().toISOString() }
      mockedAxios.get.mockResolvedValue({ data: mockUser })

      const result = await usersApi.get(1)
      expect(result).toEqual(mockUser)
      expect(mockedAxios.get).toHaveBeenCalledWith('/users/1')
    })

    it('lists users', async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 1,
        page_size: 50,
        total_pages: 0,
      }
      mockedAxios.get.mockResolvedValue({ data: mockResponse })

      const result = await usersApi.list(1, 50)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('chatsApi', () => {
    it('creates chat', async () => {
      const mockChat = { id: 1, type: 'group' as const, title: 'Test Chat', created_at: new Date().toISOString() }
      mockedAxios.post.mockResolvedValue({ data: mockChat })

      const result = await chatsApi.create('group', 'Test Chat', [1])
      expect(result).toEqual(mockChat)
    })

    it('gets chat by id', async () => {
      const mockChat = { id: 1, type: 'group' as const, title: 'Test Chat', created_at: new Date().toISOString() }
      mockedAxios.get.mockResolvedValue({ data: mockChat })

      const result = await chatsApi.get(1)
      expect(result).toEqual(mockChat)
    })
  })

  describe('messagesApi', () => {
    it('sends message', async () => {
      const mockMessage = {
        id: 1,
        chat_id: 1,
        sender_id: 1,
        body: 'Test message',
        created_at: new Date().toISOString(),
        edited_at: null,
        reply_to_id: null,
      }
      mockedAxios.post.mockResolvedValue({ data: mockMessage })

      const result = await messagesApi.send(1, 'Test message', 1)
      expect(result).toEqual(mockMessage)
    })

    it('lists messages', async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 1,
        page_size: 50,
        total_pages: 0,
      }
      mockedAxios.get.mockResolvedValue({ data: mockResponse })

      const result = await messagesApi.list(1, 1, 50)
      expect(result).toEqual(mockResponse)
    })
  })
})

