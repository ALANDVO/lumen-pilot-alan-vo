import { useEffect, useState } from 'react'
import { api, DeviceInfo } from '../api/client'

function Devices() {
  const [devices, setDevices] = useState<DeviceInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchDevices() {
      try {
        const data = await api.devices.list()
        setDevices(data.devices)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load devices')
      } finally {
        setLoading(false)
      }
    }
    fetchDevices()
  }, [])

  if (loading) {
    return (
      <div className="card">
        <div className="empty-state">Loading devices...</div>
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
      <h1 className="page-title">Devices</h1>
      <div className="card">
        <h2 className="card-title">Connected iOS Devices</h2>
        {devices.length === 0 ? (
          <div className="empty-state">
            <p>No devices connected. Connect an iOS device via USB to see it here.</p>
            <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
              Note: Device detection requires usbmuxd running on the host.
            </p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>UDID</th>
                  <th>iOS Version</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {devices.map((device) => (
                  <tr key={device.udid}>
                    <td>{device.name}</td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{device.udid}</td>
                    <td>{device.os_version}</td>
                    <td><span className={`status-badge status-${device.status.toLowerCase()}`}>{device.status}</span></td>
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

export default Devices