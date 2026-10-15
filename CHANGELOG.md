# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-15

### Added
- FastAPI backend with health check endpoint (`/api/v1/healthz`)
- React + TypeScript + Vite frontend with dashboard, devices, builds, and deployments pages
- Typed API client with full endpoint coverage
- Docker Compose orchestration for backend and frontend
- Backend tests (pytest + httpx) for health, devices, builds, deployments (11 tests)
- Frontend tests (vitest + React Testing Library) for navigation and build creation (5 tests)
- SQLite persistence with SQLAlchemy async and cross-database UUID support
- CORS configuration for local development
- Non-root Docker users and healthchecks
- Project documentation (README, LICENSE, .env.example)

### Infrastructure
- GitHub Actions CI workflow (backend pytest, frontend build/test, Docker builds)
- pyproject.toml with project metadata
- portfolio.json for portfolio tracking

### Backend Services
- DeviceService: usbmuxd device scanning and sync (`idevice_id`, `ideviceinfo`)
- BuildService: SwiftPM build orchestration with async subprocess execution
- DeploymentService: App bundle installation and launch via `ideviceinstaller`/`idevicedebug`
- LLMAdvisory: Multi-provider build failure analysis (OpenAI-compatible, Anthropic, Gemini, Ollama)

### API Endpoints
- `GET /api/v1/healthz` - Service health check
- `GET /api/v1/devices` - List connected iOS devices
- `POST /api/v1/devices/sync` - Scan and sync devices from usbmuxd
- `GET /api/v1/devices/{udid}` - Get device details
- `POST /api/v1/builds` - Create new build job
- `GET /api/v1/builds` - List builds with pagination
- `GET /api/v1/builds/{id}` - Get build details
- `POST /api/v1/builds/{id}/execute` - Execute build with optional LLM advisory
- `POST /api/v1/deployments` - Create new deployment
- `GET /api/v1/deployments` - List deployments with pagination
- `GET /api/v1/deployments/{id}` - Get deployment details
- `POST /api/v1/deployments/{id}/execute` - Execute deployment to device

### Frontend Pages
- Dashboard: System health, quick actions, product description
- Devices: Device list with sync button, empty state
- Builds: Create build form, build history table, execute with advisory
- Deployments: Create deployment form, deployment history table, execute