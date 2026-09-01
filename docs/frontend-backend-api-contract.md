# AcademIQ Backend API Contract

This document outlines the Phase E2 API contract for the AcademIQ Dashboard frontend.

## Execution Modes

All security endpoints return an explicit `execution_mode` to distinguish the data's origin and truthfulness.

```json
{
  "REAL_RUNTIME": "Live inference/execution using native systems or real models",
  "SIMULATED": "Replayed JSONL telemetry or mock environments (e.g., Windows L3)",
  "BENCHMARK": "Stored evaluation metrics representing static results",
  "SYNTHETIC": "Metrics derived from artificially synthesized datasets",
  "UNAVAILABLE": "Components that cannot be executed in the current environment"
}
```

## Endpoints

### 1. Health Check
`GET /api/health`

Returns the operational status of the backend components.

**Response**
```json
{
  "status": "healthy",
  "timestamp": "1788025376.98",
  "components": {
    "orchestrator": true,
    "experiment_results": true,
    "eces_sqlite": true
  }
}
```

### 2. Run Pipeline Scenario
`POST /api/pipeline/run`

Executes a predefined scenario through the L1-L7 security pipeline.

**Request**
```json
{
  "scenario_id": "SAFE_READ"
}
```
*Valid scenarios: SAFE_READ, FORBIDDEN_TOOL, OBFUSCATED_COMMAND, MULTISTEP_RISKCHAIN*

**Response (`PipelineRunResponse`)**
```json
{
  "session_id": "uuid",
  "scenario_id": "SAFE_READ",
  "overall_decision": "ALLOW|BLOCK|FREEZE",
  "stopping_layer": "L1|L2|L5",
  "total_latency_ns": 1500000.0,
  "L1": {
    "decision": "ALLOW|BLOCK",
    "latency": 150000.0,
    "metadata": {"tool_name": "read_file"}
  },
  "L2": {
    "decision": "ALLOW|BLOCK|null",
    "normalized_command": "cat /tmp/safe_file.txt",
    "detection_reason": null,
    "latency": 225000.0
  },
  "L3": {
    "status": "MOCKED",
    "event_count": 15,
    "anomalies": 0,
    "execution_mode": "SIMULATED"
  },
  "L4": {
    "isolation_forest_score": 0.15,
    "siamese_score": 0.08,
    "ensemble_score": 0.11,
    "drift_state": "NOMINAL",
    "execution_mode": "SIMULATED"
  },
  "L5": {
    "bayesian_probability": 0.15,
    "governance_state": "ALLOW",
    "highest_risk_path": "N/A",
    "cross_session_status": "CLEAN"
  },
  "L6": {
    "evidence_chain_reference": "chain-uuid",
    "chain_status": "APPENDED",
    "storage_backend": "SQLite"
  },
  "L7": {
    "isolation_status": "UNAVAILABLE",
    "scope_information": null
  }
}
```
*Note: If `stopping_layer` is reached early (e.g. L1), subsequent layer outputs will be gracefully represented with `null` values.*

### 3. Retrieve ECES Sessions
`GET /api/evidence/sessions`

**Response**
```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "event_count": 5,
      "start_time_ns": 1788025376000000000,
      "execution_mode": "REAL_RUNTIME"
    }
  ]
}
```

### 4. Verify Session Chain
`POST /api/evidence/session/{session_id}/verify`

**Response**
```json
{
  "session_id": "uuid",
  "valid": true,
  "records_checked": 5,
  "failure": null,
  "execution_mode": "REAL_RUNTIME"
}
```

### 5. View Experiment Summary All
`GET /api/experiments/summary/all`

**Response**
```json
{
  "experiments": [
    {
      "id": "exp1_direct_prompt_injection",
      "detection_rate": 0.95,
      "asr": 0.05,
      "latency_ms": 1.2,
      "execution_type": "BENCHMARK"
    }
  ]
}
```

### 6. View Specific Experiment Detail
`GET /api/experiments/{experiment_id}`

**Response**
```json
{
  "experiment_id": "exp1_direct_prompt_injection",
  "title": "Exp1 Direct Prompt Injection",
  "execution_type": "BENCHMARK",
  "sample_size": 140,
  "metrics": {...},
  "latency_metrics": {...},
  "limitations": "Native execution not validated. Tests performed in Windows simulation.",
  "artifact_paths": ["benchmarks/results/exp1/summary.json"],
  "timestamp": "1788025376"
}
```

## Error Handling
The backend will return standard HTTP errors:
- `400 Bad Request` for invalid scenario IDs.
- `404 Not Found` for non-existent experiments or sessions.
- `500 Internal Server Error` on backend exceptions.
