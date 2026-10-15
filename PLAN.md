# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

core-skeleton

## Roadmap

### core-skeleton — FastAPI/React skeleton with health check workflow

Status: done

Acceptance:
- Backend FastAPI app starts and responds to /healthz
- Frontend Vite+React+TS app builds and serves
- Docker compose brings up both services
- Backend tests pass (pytest)
- Frontend typecheck and tests pass (vitest)

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/api/health.py`, `backend/app/api/devices.py`, `backend/app/api/builds.py`, `backend/app/api/deployments.py`, `backend/app/models/__init__.py`, `backend/app/services/device_service.py`, `backend/app/services/build_service.py`, `backend/app/services/deployment_service.py`, `backend/app/services/llm_advisory.py`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/Devices.tsx`, `frontend/src/pages/Builds.tsx`, `frontend/src/pages/Deployments.tsx`, `frontend/src/api/client.ts`, `frontend/src/index.css`, `frontend/src/App.css`, `compose.yaml`, `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`

Tests: `backend/tests/test_health.py`, `backend/tests/test_devices.py`, `backend/tests/test_builds.py`, `backend/tests/test_deployments.py`, `frontend/src/App.test.tsx`

### device-management — iOS device detection and connection workflow

Status: planned

Acceptance:
- API lists connected iOS devices via usbmuxd
- Frontend shows device list with status
- User can select device for deployment

### swiftpm-build — SwiftPM build orchestration workflow

Status: planned

Acceptance:
- API accepts SwiftPM project path and build configuration
- Backend executes swift build for iOS target
- Frontend shows build progress and logs
- Build artifacts accessible for deployment

### app-deployment — App installation and launch workflow

Status: planned

Acceptance:
- API installs .app bundle to selected device
- Frontend triggers install and shows progress
- App launches on device with debug logging

### auth-oidc — OIDC authentication with Keycloak

Status: planned

Acceptance:
- Backend validates Keycloak tokens
- Frontend PKCE login flow works
- Protected endpoints require authentication
- Roles: viewer, operator, admin

### llm-advisory — LLM advisory for build failures

Status: planned

Acceptance:
- Opt-in LLM analysis of build errors
- Supports OpenAI-compatible, Anthropic, Gemini, Ollama
- Advisory responses labeled and grounded in logs

