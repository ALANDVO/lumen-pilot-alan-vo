const API_BASE = '/api/v1'

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }))
    throw new Error(error.message || `HTTP ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

export interface DeviceInfo {
  udid: string
  name: string
  os_version: string
  status: string
}

export interface DeviceListResponse {
  devices: DeviceInfo[]
}

export interface BuildRequest {
  project_path: string
  configuration?: string
  target?: string
}

export interface BuildResponse {
  id: string
  project_path: string
  configuration: string
  target: string
  status: string
  created_at: string
  completed_at: string | null
  log: string
}

export interface BuildListResponse {
  builds: BuildResponse[]
}

export interface AdvisoryResponse {
  provider: string
  model: string
  summary: string
  suggestions: string[]
  timestamp: string
  advisory: boolean
}

export interface BuildExecuteResponse {
  build: BuildResponse
  advisory: AdvisoryResponse | null
}

export interface DeploymentRequest {
  build_id: string
  device_udid: string
}

export interface DeploymentResponse {
  id: string
  build_id: string
  device_udid: string
  status: string
  created_at: string
  completed_at: string | null
  log: string
}

export interface DeploymentListResponse {
  deployments: DeploymentResponse[]
}

export interface HealthResponse {
  status: string
  service: string
  version: string
}

export const api = {
  health: {
    check: () => request<HealthResponse>('/healthz'),
  },
  devices: {
    list: () => request<DeviceListResponse>('/devices'),
  },
  builds: {
    create: (data: BuildRequest) => request<BuildResponse>('/builds', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    list: () => request<BuildListResponse>('/builds'),
    get: (id: string) => request<BuildResponse>(`/builds/${id}`),
    execute: (id: string) => request<BuildExecuteResponse>(`/builds/${id}/execute`, {
      method: 'POST',
    }),
  },
  deployments: {
    create: (data: DeploymentRequest) => request<DeploymentResponse>('/deployments', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    list: () => request<DeploymentListResponse>('/deployments'),
    get: (id: string) => request<DeploymentResponse>(`/deployments/${id}`),
    execute: (id: string) => request<DeploymentResponse>(`/deployments/${id}/execute`, {
      method: 'POST',
    }),
  },
}