# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

project-skeleton

## Roadmap

### project-skeleton — Project skeleton with FastAPI/React, Docker, CI

Status: done

Acceptance:
- Backend FastAPI app runs with SQLite
- Frontend React+TS+Vite builds and runs
- Docker compose with backend, frontend, Keycloak
- CI workflow runs backend/frontend tests
- Basic project structure with all required files

Implementation: `backend/app/main.py`, `backend/app/api/actors.py`, `backend/app/api/auth.py`, `backend/app/api/telemetry.py`, `backend/app/api/snapshots.py`, `backend/app/api/health.py`, `backend/app/services/actor.py`, `backend/app/services/telemetry.py`, `backend/app/services/snapshot.py`, `backend/app/services/user.py`, `backend/app/models/actor.py`, `backend/app/models/snapshot.py`, `backend/app/models/telemetry.py`, `backend/app/models/user.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/auth.py`, `backend/app/core/security.py`, `backend/requirements.txt`, `backend/Dockerfile`, `backend/tests/test_actor.py`, `backend/tests/test_api.py`, `backend/tests/test_auth.py`, `backend/tests/test_health.py`, `backend/tests/test_telemetry.py`, `frontend/package.json`, `frontend/tsconfig.json`, `frontend/vite.config.ts`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`, `frontend/src/hooks/useAuth.ts`, `frontend/src/hooks/useActors.ts`, `frontend/src/hooks/useTelemetry.ts`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/Actors.tsx`, `frontend/src/pages/Telemetry.tsx`, `frontend/src/pages/Alerts.tsx`, `frontend/src/pages/Settings.tsx`, `frontend/src/pages/Login.tsx`, `frontend/Dockerfile`, `compose.yaml`, `.github/workflows/ci.yml`, `portfolio.json`, `README.md`, `LICENSE`, `CHANGELOG.md`, `pyproject.toml`, `.gitignore`, `.env.example`

Tests: `backend/tests/test_actor.py`, `backend/tests/test_api.py`, `backend/tests/test_auth.py`, `backend/tests/test_health.py`, `backend/tests/test_telemetry.py`

### actor-state-machine — Actor state machine domain engine

Status: planned

Acceptance:
- Actor model with RUNNING/PAUSED/SUSPENDED/CRASHED states
- State transition API with validation
- Snapshot management (full/data scopes)
- Actor CRUD and lifecycle endpoints

### oidc-auth — OIDC authentication with Keycloak

Status: planned

Acceptance:
- SPA PKCE flow with in-memory tokens
- Backend token validation
- Role-based authorization (viewer/operator/admin)
- Login/logout flows working

### telemetry-dashboard — Telemetry dashboard with actor metrics

Status: planned

Acceptance:
- Actor count gauge by status/template
- Crash counter metric
- Per-template telemetry attribution display
- Bounded cardinality metric visualization

### self-suspend-workflow — Actor self-suspend cooperative workflow

Status: planned

Acceptance:
- Actors can yield via well-known file
- Pause endpoint triggers snapshot
- Timer-based auto-escalation to SUSPENDED

