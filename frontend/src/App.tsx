import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Devices from './pages/Devices'
import Builds from './pages/Builds'
import Deployments from './pages/Deployments'
import './App.css'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Lumen Pilot</h1>
        <nav>
          <ul>
            <li><a href="/">Dashboard</a></li>
            <li><a href="/devices">Devices</a></li>
            <li><a href="/builds">Builds</a></li>
            <li><a href="/deployments">Deployments</a></li>
          </ul>
        </nav>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/devices" element={<Devices />} />
          <Route path="/builds" element={<Builds />} />
          <Route path="/deployments" element={<Deployments />} />
        </Routes>
      </main>
    </div>
  )
}

export default App