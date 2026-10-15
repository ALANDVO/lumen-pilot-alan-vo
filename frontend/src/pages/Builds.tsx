import { useEffect, useState } from 'react'
import { api, BuildRequest, BuildResponse } from '../api/client'

function Builds() {
  const [builds, setBuilds] = useState<BuildResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [formData, setFormData] = useState<BuildRequest>({
    project_path: '',
    configuration: 'debug',
    target: 'ios',
  })

  useEffect(() => {
    fetchBuilds()
  }, [])

  async function fetchBuilds() {
    try {
      const data = await api.builds.list()
      setBuilds(data.builds)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load builds')
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!formData.project_path.trim()) return

    setCreating(true)
    setError(null)
    try {
      await api.builds.create(formData)
      setFormData({ project_path: '', configuration: 'debug', target: 'ios' })
      await fetchBuilds()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create build')
    } finally {
      setCreating(false)
    }
  }

  if (loading) {
    return (
      <div className="card">
        <div className="empty-state">Loading builds...</div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="page-title">Builds</h1>
      <div className="card">
        <h2 className="card-title">Create New Build</h2>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '600px' }}>
          <div className="form-group">
            <label className="form-label" htmlFor="project_path">Project Path</label>
            <input
              type="text"
              id="project_path"
              className="form-input"
              placeholder="/path/to/SwiftPM/project"
              value={formData.project_path}
              onChange={(e) => setFormData({ ...formData, project_path: e.target.value })}
              required
            />
          </div>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <div className="form-group" style={{ flex: 1, minWidth: '200px' }}>
              <label className="form-label" htmlFor="configuration">Configuration</label>
              <select
                id="configuration"
                className="form-input"
                value={formData.configuration}
                onChange={(e) => setFormData({ ...formData, configuration: e.target.value })}
              >
                <option value="debug">Debug</option>
                <option value="release">Release</option>
              </select>
            </div>
            <div className="form-group" style={{ flex: 1, minWidth: '200px' }}>
              <label className="form-label" htmlFor="target">Target</label>
              <select
                id="target"
                className="form-input"
                value={formData.target}
                onChange={(e) => setFormData({ ...formData, target: e.target.value })}
              >
                <option value="ios">iOS Device</option>
                <option value="ios-simulator">iOS Simulator</option>
              </select>
            </div>
          </div>
          <button type="submit" className="btn btn-primary" disabled={creating} style={{ width: 'fit-content' }}>
            {creating ? 'Creating...' : 'Create Build'}
          </button>
          {error && <p style={{ color: '#dc3545' }}>{error}</p>}
        </form>
      </div>
      <div className="card">
        <h2 className="card-title">Build History</h2>
        {builds.length === 0 ? (
          <div className="empty-state">
            <p>No builds yet. Create your first build above.</p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Project</th>
                  <th>Configuration</th>
                  <th>Target</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {builds.map((build) => (
                  <tr key={build.id}>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{build.id.slice(0, 8)}…</td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{build.project_path}</td>
                    <td>{build.configuration}</td>
                    <td>{build.target}</td>
                    <td><span className={`status-badge status-${build.status.toLowerCase()}`}>{build.status}</span></td>
                    <td>{new Date(build.created_at).toLocaleString()}</td>
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

export default Builds