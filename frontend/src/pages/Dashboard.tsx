import { useEffect, useState } from 'react'
import { api, HealthResponse } from '../api/client'

function Dashboard() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchHealth() {
      try {
        const data = await api.health.check()
        setHealth(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load health')
      } finally {
        setLoading(false)
      }
    }
    fetchHealth()
  }, [])

  if (loading) {
    return (
      <div className="card">
        <div className="empty-state">Loading...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card">
        <div className="empty-state">
          <h2>Error</h2>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="page-title">Dashboard</h1>
      <div className="card">
        <h2 className="card-title">System Status</h2>
        {health && (
          <dl style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.5rem 1.5rem' }}>
            <dt>Status</dt>
            <dd><span className={`status-badge status-${health.status}`}>{health.status}</span></dd>
            <dt>Service</dt>
            <dd>{health.service}</dd>
            <dt>Version</dt>
            <dd>{health.version}</dd>
          </dl>
        )}
      </div>
      <div className="card">
        <h2 className="card-title">Quick Actions</h2>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <a href="/devices" className="btn btn-primary">View Devices</a>
          <a href="/builds" className="btn btn-secondary">Manage Builds</a>
          <a href="/deployments" className="btn btn-secondary">Deployments</a>
        </div>
      </div>
      <div className="card">
        <h2 className="card-title">About Lumen Pilot</h2>
        <p style={{ color: '#4a4a6a', lineHeight: 1.7 }}>
          Lumen Pilot is a cross-platform Xcode replacement for building and deploying iOS apps
          with SwiftPM on Linux, Windows, and macOS. It provides a web-based interface for
          managing iOS device connections, SwiftPM builds, and app deployments.
        </p>
        <p style={{ color: '#4a4a6a', lineHeight: 1.7, marginTop: '1rem' }}>
          This dashboard shows the backend API health. Navigate to Devices to see connected
          iOS devices, Builds to manage SwiftPM project builds, and Deployments to install
          and launch apps on physical devices.
        </p>
      </div>
    </div>
  )
}

export default Dashboard