# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-22

### Added
- Initial release of Orbit Console for Agent Substrate
- Actor lifecycle management (create, pause, resume, commit, revert, dump)
- Validated state machine transitions: RUNNING ↔ PAUSED ↔ SUSPENDED ↔ CRASHED
- Snapshot management with full/data scopes and tagging
- Telemetry dashboard with bounded cardinality metrics
  - `ate.actors` gauge by status × template
  - `ate.actor.crashes` counter by template
  - State transition tracking
- OIDC authentication with Keycloak (PKCE flow)
- Role-based access control (viewer, operator, admin)
- React + TypeScript + Vite frontend with responsive UI
- FastAPI + SQLAlchemy backend with SQLite/PostgreSQL
- Docker Compose with Keycloak, backend, frontend
- CI/CD pipeline with backend/frontend tests and Docker builds

### Security
- JWT-based authentication with HS256
- PKCE authorization code flow
- CORS configured for frontend origin
- Non-root Docker users
- Health checks on all services

### Known Limitations
- Demo mode uses plain PKCE challenge (S256 recommended for production)
- Token stored in localStorage (httpOnly cookie preferred for production)
- SQLite default; PostgreSQL recommended for production
- Rate limiting not implemented
- SAML broker configuration documented but not tested