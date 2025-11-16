import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import Login from '../Login'
import { usersApi } from '../../api/client'
import { useAuthStore } from '../../store/authStore'

vi.mock('../../api/client')
vi.mock('../../store/authStore')
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  const mockNavigate = vi.fn()
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

describe('Login', () => {
  const mockLogin = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useAuthStore).mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: mockLogin,
      logout: vi.fn(),
    } as any)
  })

  it('renders login form', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )
    
    expect(screen.getByLabelText(/handle/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/nombre para mostrar/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument()
  })

  it('submits form with valid data', async () => {
    const user = userEvent.setup()
    const mockUser = { id: 1, handle: 'testuser', display_name: 'Test User', created_at: new Date().toISOString() }
    
    vi.mocked(usersApi.create).mockResolvedValue(mockUser)

    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )

    await user.type(screen.getByLabelText(/handle/i), 'testuser')
    await user.type(screen.getByLabelText(/nombre para mostrar/i), 'Test User')
    await user.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(usersApi.create).toHaveBeenCalledWith('testuser', 'Test User')
    })
    
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled()
    })
  })

  it('shows error on duplicate handle', async () => {
    const user = userEvent.setup()
    const error: any = { response: { status: 409 } }
    
    vi.mocked(usersApi.create).mockRejectedValue(error)

    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )

    await user.type(screen.getByLabelText(/handle/i), 'testuser')
    await user.type(screen.getByLabelText(/nombre para mostrar/i), 'Test User')
    await user.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(screen.getByText(/este handle ya existe/i)).toBeInTheDocument()
    })
  })
})
