# Phase E4.4: System Status & Architecture Health Dashboard

## Overview
Phase E4.4 focused on building the final major dashboard view that gives a truthful, real-time architectural status of the AcademIQ system. 

The primary requirement for this dashboard is **scientific honesty**. The dashboard strictly differentiates between native implementations, simulated telemetry replays, and synthetically benchmarked components. 

## Backend Implementation

The backend was extended with a new endpoint to query system health and capability availability:

- **Endpoint**: `GET /api/system/status`
- **Location**: `dashboard_api/routers/status.py`
- **Service Logic**: `dashboard_api/services/status_service.py`
- **Schemas**: `dashboard_api/schemas/status.py`

### System Health Logic
1. **ECES Database Availability**: The service tests accessibility of the SQLite database by running a `SELECT 1` query to verify that it is actually readable, rather than just asserting that the `.db` file exists.
2. **Infrastructure**: Reports the health of the Dashboard API, Pipeline Engine, ECES database, and Native Runtime Telemetry (which explicitly reports `UNAVAILABLE`).
3. **L1-L7 Architecture Grid**: A dynamically generated grid showing the operational status and execution mode of each security layer. For example, L3 Runtime Telemetry is explicitly reported as `SIMULATED` because native eBPF is currently unvalidated on Windows.
4. **Capability Matrix**: Maps specific functional capabilities (like Prompt Injection Defense, Native OS Isolation) to their respective implementation and validation levels.

## Frontend Implementation

The frontend replaces the existing placeholder with a clean, dark-themed, and responsive dashboard.

- **Component Structure**:
  - `SystemStatusPage.tsx`: The primary container and layout composition.
  - `InfrastructureStatusGrid.tsx`: Visualizes API, Database, and Telemetry infrastructure health.
  - `LayerStatusGrid.tsx`: Visualizes the 7 layers, mapping their respective execution modes, capabilities, and limitations.
  - `CapabilityMatrix.tsx`: A matrix cross-referencing capabilities against their validation strategy and execution mode.

- **Visual Distinctions**:
  - Employs the `ExecutionModeBadge` introduced in earlier phases to provide visual consistency (`REAL_RUNTIME` vs `SIMULATED` vs `BENCHMARK`).
  - Unavailable infrastructure is gracefully rendered in red/gray tones without implying the entire application is broken.

## Testing & Validation
- **Backend**: Tested using `pytest tests/dashboard_api/test_status.py`. Asserts that `UNAVAILABLE` layers are strictly enforced and capabilities contain no fabricated metrics.
- **Frontend**: Tested using `vitest run src/tests/SystemStatusPage.test.tsx`. Validates accurate rendering of all capability rows, layer states, and UI fallbacks in error states.

## Known Limitations
- The system status is currently heavily derived from static configuration to enforce truthfulness regarding the current project state (i.e. Windows constraints). In a fully distributed deployment, these values would be queried dynamically across a message bus or node agent.
