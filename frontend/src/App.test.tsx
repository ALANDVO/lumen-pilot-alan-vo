import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import App from './App'
import { api } from './api/client'

vi.mock('./api/client', () => ({
  api: {
    health: {
      check: vi.fn(),
    },
    devices: {
      list: vi.fn(),
    },
    builds: {
      list: vi.fn(),
      create: vi.fn(),
    },
    deployments: {
      list: vi.fn(),
      create: vi.fn(),
    },
  },
}))

const mockHealthCheck = api.health.check as vi.Mock
const mockDevicesList = api.devices.list as vi.Mock
const mockBuildsList = api.builds.list as vi.Mock
const mockBuildsCreate = api.builds.create as vi.Mock
const mockDeploymentsList = api.deployments.list as vi.Mock

function renderApp(initialEntries: string[] = ['/']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <App />
    </MemoryRouter>
  )
}

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockHealthCheck.mockResolvedValue({ status: 'ok', service: 'lumen-pilot', version: '1.0.0' })
    mockDevicesList.mockResolvedValue({ devices: [] })
    mockBuildsList.mockResolvedValue({ builds: [] })
    mockDeploymentsList.mockResolvedValue({ deployments: [] })
  })

  it('renders dashboard with health status', async () => {
    renderApp(['/'])
    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })
    await waitFor(() => {
      expect(screen.getByText('System Status')).toBeInTheDocument()
    })
    expect(screen.getByText('ok')).toBeInTheDocument()
  })

  it('navigates to devices page', async () => {
    renderApp(['/devices'])
    await waitFor(() => {
      expect(screen.getByText('Connected iOS Devices')).toBeInTheDocument()
    })
  })

  it('navigates to builds page', async () => {
    renderApp(['/builds'])
    await waitFor(() => {
      expect(screen.getByText('Create New Build')).toBeInTheDocument()
    })
  })

  it('navigates to deployments page', async () => {
    renderApp(['/deployments'])
    await waitFor(() => {
      expect(screen.getByText('Create New Deployment')).toBeInTheDocument()
    })
  })
})

describe('Builds page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockHealthCheck.mockResolvedValue({ status: 'ok', service: 'lumen-pilot', version: '1.0.0' })
    mockDevicesList.mockResolvedValue({ devices: [] })
    mockBuildsList.mockResolvedValue({ builds: [] })
    mockBuildsCreate.mockResolvedValue({
      id: 'test-id',
      project_path: '/test/path',
      configuration: 'debug',
      target: 'ios',
      status: 'pending',
      created_at: new Date().toISOString(),
      completed_at: null,
      log: '',
    })
    mockDeploymentsList.mockResolvedValue({ deployments: [] })
  })

  it('creates a new build', async () => {
    const user = userEvent.setup()
    renderApp(['/builds'])
    await waitFor(() => {
      expect(screen.getByText('Create New Build')).toBeInTheDocument()
    })
    await user.type(screen.getByLabelText(/project path/i), '/path/to/project')
    await user.click(screen.getByRole('button', { name: /create build/i }))
    await waitFor(() => {
      expect(mockBuildsCreate).toHaveBeenCalledWith({
        project_path: '/path/to/project',
        configuration: 'debug',
        target: 'ios',
      })
    })
  })
})