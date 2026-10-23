import { useEffect, useState } from 'react'
import { api, BuildRequest, BuildResponse, AdvisoryResponse } from '../api/client'

function Builds() {
  const [builds, setBuilds] = useState<BuildResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [executing, setExecuting] = useState<string | null>(null)
  const [advisory, setAdvisory] = useState<AdvisoryResponse | null>(null)
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

  async function handleExecute(buildId: string) {
    setExecuting(buildId)
    setAdvisory(null)
    setError(null)
    try {
      const result = await api.builds.execute(buildId)
      if (result.advisory) {
        setAdvisory(result.advisory)
      }
      await fetchBuilds()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute build')
    } finally {
      setExecuting(null)
    }
  }

  function handleAdvisoryClose() {
    setAdvisory(null)
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
                  <th>Actions</th>
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
                    <td>
                      <button
                        className="btn btn-secondary"
                        onClick={() => handleExecute(build.id)}
                        disabled={executing === build.id || build.status === 'running'}
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.875rem' }}
                      >
                        {executing === build.id ? 'Executing...' : 'Execute'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {advisory && (
        <div className="card" style={{ borderColor: '#ffc107', marginTop: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 className="card-title" style={{ margin: 0, color: '#856404' }}>LLM Advisory</h2>
            <button onClick={handleAdvisoryClose} style={{ background: 'none', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: '#856404' }}>×</button>
          </div>
          <div style={{ background: '#fff3cd', padding: '1rem', borderRadius: '4px', border: '1px solid #ffc107' }}>
            <p style={{ margin: '0 0 0.5rem', fontWeight: 600, color: '#856404' }}>
              Provider: {advisory.provider} ({advisory.model}) — Advisory
            </p>
            <p style={{ margin: '0 0 1rem', color: '#856404' }}>{advisory.summary}</p>
            {advisory.suggestions.length > 0 && (
              <ul style={{ margin: 0, paddingLeft: '1.5rem', color: '#856404' }}>
                {advisory.suggestions.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            )}
            <p style={{ margin: '1rem 0 0', fontSize: '0.875rem', color: '#856404' }}>
              Generated at {new Date(advisory.timestamp).toLocaleString()}. This is an AI-generated advisory; verify before applying.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default Builds