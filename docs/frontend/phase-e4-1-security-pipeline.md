# Phase E4.1: Live Security Pipeline View Final Report

## 1. Files Created
- `frontend/src/types/pipeline.ts`
- `frontend/src/hooks/usePipelineExecution.ts`
- `frontend/src/components/pipeline/ScenarioSelector.tsx`
- `frontend/src/components/pipeline/PipelineLayerCard.tsx`
- `frontend/src/components/pipeline/PipelineFlow.tsx`
- `frontend/src/tests/PipelinePage.test.tsx`
- `docs/frontend/phase-e4-1-security-pipeline.md`

## 2. Files Modified
- `frontend/src/pages/PipelinePage.tsx`
- `frontend/src/components/common/ExecutionModeBadge.tsx` (Minor adjustments)

## 3. Existing Frontend Components Reused
- `ExecutionModeBadge`
- `StatusBadge`
- `ErrorState`

## 4. Existing Backend APIs Reused
- `POST /api/pipeline/run`

## 5. Exact API Request/Response Flow
1. **Request:** The user clicks a scenario in `ScenarioSelector`. `usePipelineExecution` sends a POST request with `{"scenario_id": "<SCENARIO_ID>"}` via Axios to the backend endpoint.
2. **Backend Processing:** The backend `PipelineService` processes the request synchronously through the `AcademiqOrchestrator` simulation and returns the complete result instantly.
3. **Response Validation:** The Axios client casts the response to the strict `PipelineRunResponse` TypeScript interface.

## 6. How each L1–L7 layer is mapped
Each layer is rendered using `PipelineLayerCard`. The frontend state machine (`usePipelineExecution`) steps through the keys `L1`-`L7` in the `PipelineRunResponse`.
- **L1 (Grammar):** Displays the parsed `decision` and `latency`.
- **L2 (Semantic):** Displays `normalized_command` and `detection_reason`.
- **L3 (Telemetry):** Maps `event_count` and `anomalies`.
- **L4 (Divergence):** Maps Isolation Forest, Siamese, and Ensemble scores.
- **L5 (RiskChain):** Maps `bayesian_probability` and `cross_session_status`.
- **L6 (ECES):** Maps `evidence_chain_reference` and storage backend.
- **L7 (Isolation):** Maps `isolation_status`.

## 7. How stopping layer detection works
The backend explicitly returns `stopping_layer` and `overall_decision`. If the pipeline encounters a `'BLOCK'` or `'FREEZE'` decision from a layer (as processed in the UI step-through loop), the animation terminates, and an overarching "ATTACK INTERCEPTED" banner is displayed highlighting the stopping layer and the total pipeline latency.

## 8. How ExecutionMode truthfulness is enforced
The API returns `execution_mode` (e.g., `REAL_RUNTIME`, `SIMULATED`, `UNAVAILABLE`) dynamically for relevant layers (L3, L4). The `PipelineFlow` component passes this value strictly down to the `ExecutionModeBadge`. No hardcoding is permitted; if `execution_mode` is missing, it cascades or defaults strictly to `UNAVAILABLE`. For example, L3 (eBPF) native execution defaults to `UNAVAILABLE` on Windows.

## 9. How missing/unavailable layers are handled
If a layer object in the API response is `null` or explicitly returns a state mapping to `UNAVAILABLE` (e.g., L2 bypassed because L1 blocked, or L7 lacking OS support), the state machine sets it to `UNAVAILABLE`. The `PipelineLayerCard` renders this with a gray, dashed outline and explicitly labels it unavailable.

## 10. Execution Streaming vs UI Playback
**UI Playback.** The API endpoint is strictly synchronous and HTTP-based (no WebSockets/SSE). The frontend `usePipelineExecution` hook simulates a "live" execution sequence by awaiting an artificial 500ms delay between updating each layer state (`PENDING` -> `PROCESSING` -> `ALLOW`/`BLOCK`). This is a visual aid for the demo/dashboard, and is explicitly stated in the UI under "Execution Notes".

## 11. Screens/Pages Implemented
- **Security Pipeline (`/pipeline`):** The interactive scenario executor and L1-L7 visual trace graph.

## 12. Tests Added
- `PipelinePage.test.tsx`: Validates rendering of scenarios, default idle state, click handlers, and asynchronous simulation flow execution where layer states shift from `PENDING` to `ALLOW` based on mock responses.

## 13. Build Result
`npm run build` completed successfully in ~1.24s with zero TypeScript errors.

## 14. Test Result
`npm run test` completed successfully. All components mount without crashing and business logic behaves correctly.

## 15. Known Limitations
- Real-time data streaming is not present. If long-running actions (e.g., massive eBPF traces) block the synchronous FastAPI thread, it may cause a timeout.
- Complex animation transitions between layers rely on simple React state delays rather than robust animation libraries (like Framer Motion).

## 16. Exact Commands to Run Frontend
```bash
cd frontend
npm install
npm run dev
```

## 17. Exact Commands to Run Frontend Tests
```bash
cd frontend
npm run test
```

## 18. Security Truthfulness Confirmation
**I explicitly confirm that no fake security results were generated.** Every probability score, normalized command string, latency timing, and execution decision rendered in the UI is directly passed from the backend API response without obfuscation or fabrication.
