# AcademIQ Dashboard Backend API

This is the lightweight FastAPI backend API layer (Phase E1) required for the future frontend dashboard (Phase E2). It exposes AcademIQ's existing pipeline, experiment results, and ECES evidence data.

## Architecture

```text
Frontend (Phase E2)
       │
       ▼
 FastAPI Backend (dashboard_api/)
       │
 ┌─────┼─────────────┐
 ▼     ▼             ▼
L1-L7  Benchmarks   ECES SQLite
```

## Security Constraints
- **No Arbitrary Execution**: The API cannot invoke arbitrary shell commands on the host. The pipeline endpoint (`/api/pipeline/run`) only invokes predefined safe demonstration scenarios using simulated event objects.
- **No Duplicated Logic**: The API serves strictly as an adapter/proxy. It invokes the existing `AcademiqOrchestrator`, reads the existing `benchmarks/results/*.json`, and uses the existing `l6_eces/verify_chain.py` cryptographic implementation.

## Installation

Ensure the required dependencies are installed:
```bash
pip install fastapi uvicorn pydantic
```

## Running the Backend

Start the server using `uvicorn`:
```bash
python -m uvicorn dashboard_api.main:app --reload
```

## API Endpoints

- **Health**: `GET /api/health`
- **Experiments**:
  - `GET /api/experiments` (Lists all detected experiments/techniques)
  - `GET /api/experiments/summary/all` (Aggregates high-level metrics)
  - `GET /api/experiments/{id}` (Returns specific experiment summary and metrics)
- **Pipeline**:
  - `POST /api/pipeline/run` (Invokes predefined safe scenario)
- **Evidence**:
  - `GET /api/evidence/sessions` (Lists all sessions in `eces.db`)
  - `GET /api/evidence/session/{session_id}` (Returns the complete evidence chain)
  - `POST /api/evidence/session/{session_id}/verify` (Cryptographically verifies the chain)

## Interactive API Documentation

Once the server is running, visit:
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- OpenAPI JSON: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
