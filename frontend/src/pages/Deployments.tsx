import { useEffect, useState } from 'react'
import { api, DeploymentRequest, DeploymentResponse } from '../api/client'

function Deployments() {
  const [deployments, setDeployments] = useState<DeploymentResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [formData, setFormData] = useState<DeploymentRequest>({
    build_id: '',
    device_udid: '',
  })

  useEffect(() => {
    fetchDeployments()
  }, [])

  async function fetchDeployments() {
    try {
      const data = await api.deployments.list()
      setDeployments(data.deployments)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load deployments')
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!formData.build_id.trim() || !formData.device_udid.trim()) return

    setCreating(true)
    setError(null)
    try {
      await api.deployments.create(formData)
      setFormData({ build_id: '', device_udid: '' })
      await fetchDeployments()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create deployment')
    } finally {
      setCreating(false)
    }
  }

  if (loading) {
    return (
      <div className="card">
        <div className="empty-state">Loading deployments...</div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="page-title">Deployments</h1>
      <div className="card">
        <h2 className="card-title">Create New Deployment</h2>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '600px' }}>
          <div className="form-group">
            <label className="form-label" htmlFor="build_id">Build ID</label>
            <input
              type="text"
              id="build_id"
              className="form-input"
              placeholder="UUID of the build to deploy"
              value={formData.build_id}
              onChange={(e) => setFormData({ ...formData, build_id: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="device_udid">Device UDID</label>
            <input
              type="text"
              id="device_udid"
              className="form-input"
              placeholder="UDID of target iOS device"
              value={formData.device_udid}
              onChange={(e) => setFormData({ ...formData, device_udid: e.target.value })}
              required
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={creating} style={{ width: 'fit-content' }}>
            {creating ? 'Deploying...' : 'Deploy App'}
          </button>
          {error && <p style={{ color: '#dc3545' }}>{error}</p>}
        </form>
      </div>
      <div className="card">
        <h2 className="card-title">Deployment History</h2>
        {deployments.length === 0 ? (
          <div className="empty-state">
            <p>No deployments yet. Deploy an app build to a device above.</p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Build ID</th>
                  <th>Device UDID</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {deployments.map((deployment) => (
                  <tr key={deployment.id}>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{deployment.id.slice(0, 8)}…</td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{deployment.build_id.slice(0, 8)}…</td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{deployment.device_udid}</td>
                    <td><span className={`status-badge status-${deployment.status.toLowerCase()}`}>{deployment.status}</span></td>
                    <td>{new Date(deployment.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default Deployments