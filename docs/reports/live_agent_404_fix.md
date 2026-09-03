# Live AI Agent 404 Fix Report

**Date:** 2026-09-03
**Severity:** Critical — Live AI Agent completely non-functional
**Status:** FIXED and verified

---

## 1. Exact Root Cause

**Stale server process.**
The uvicorn backend process was started BEFORE `dashboard_api/routers/agent.py` was written
during Phase C development. Python/uvicorn loads all application code at startup. Since
`agent.py` did not exist when the process started, the FastAPI app loaded with NO `/api/agent`
router registered. Every call to `POST /api/agent/chat` returned 404 Not Found, even though
the route was correctly coded in all source files.

This was a NO-CODE-CHANGE-NEEDED bug. The route, router, and frontend client were all correct.
Only the running process was stale.

---

## 2. Diagnosis Trail

### Step 1 — Backend log evidence (task-6622 started 2026-09-03T06:42:38Z)

```
INFO: "OPTIONS /api/agent/chat HTTP/1.1" 200 OK     <- CORS preflight worked
INFO: "POST   /api/agent/chat HTTP/1.1" 404 Not Found  <- Route not registered
```

### Step 2 — Frontend request path verified

- baseURL: `http://localhost:8000` (from VITE_API_BASE_URL or default)
- Call: `POST /api/agent/chat` in `frontend/src/api/agent.ts`
- No Vite proxy configured (direct cross-origin request)

### Step 3 — Backend route verified correct in source

- `dashboard_api/routers/agent.py`: `@router.post("/chat")`
- `dashboard_api/main.py`: `app.include_router(agent.router, prefix="/api/agent")`
- Full path: `POST /api/agent/chat` — correctly coded

### Step 4 — Confirmed stale process

The uvicorn process was started at 06:42:38, before agent.py was written.
It loaded the old application with no agent router.

---

## 3. Frontend Endpoint (Before Fix)

POST http://localhost:8000/api/agent/chat  (CORRECT — did not need to change)

---

## 4. Backend Endpoint (Before Fix)

The running process had NO /api/agent/chat route. Source code was correct; process was stale.

---

## 5. Why the 404 Occurred

Phase C wrote agent.py and updated main.py to register it.
The uvicorn process was already running from before Phase C.
Python loads routes at startup only (--reload was not enabled on the old process).
The running FastAPI app had no /api/agent router -> 404 on every request.

---

## 6. Files Changed

| File | Change |
|------|--------|
| tests/dashboard_api/test_agent.py | Added test_agent_chat_endpoint_is_registered_not_404 regression guard |

No application code was changed. Fix was restarting the server.

---

## 7. Exact Fix

1. Killed stale uvicorn process (task-6622)
2. Started fresh: python -m uvicorn dashboard_api.main:app --host 127.0.0.1 --port 8000 --reload
3. New process loaded main.py which correctly registers agent.router at /api/agent

---

## 8. Final Canonical Endpoint

POST http://localhost:8000/api/agent/chat
Content-Type: application/json
{"message": "Read the demo report file."}

---

## 9. Frontend -> Backend Flow (Verified End-to-End)

AgentChatPage -> useAgentExecution -> sendChatMessage()
  -> POST /api/agent/chat
  -> dashboard_api/routers/agent.py -> AgentService.process_chat()
  -> MockProvider / GeminiProvider -> generate_action()
  -> ToolInvocationEvent created
  -> AcademiqOrchestrator.process_event()
  -> L1 GCD -> L2 SDN -> L3 Telemetry -> L4 Divergence -> L5 Risk -> L6 ECES -> L7 Attestation
  -> PipelineRunResponse returned
  -> Frontend: Final Verdict Panel + PipelineFlow animation

---

## 10. Gemini / Mock Behavior

| GEMINI_API_KEY | Provider    | Notes                                          |
|----------------|-------------|------------------------------------------------|
| Not set        | Mock / Demo | Deterministic keyword-based tool call selection |
| Set            | Gemini      | Real LLM generates structured tool call        |

Both route through the full L1-L7 pipeline identically.

---

## 11. Backend Test Result

tests/dashboard_api/test_agent.py::test_agent_chat_endpoint_is_registered_not_404  PASSED
tests/dashboard_api/test_agent.py::test_agent_chat_endpoint_mock                   PASSED
tests/dashboard_api/test_agent.py::test_agent_chat_endpoint_delete                 PASSED
tests/dashboard_api/test_agent.py::test_agent_chat_endpoint_exfiltration           PASSED
tests/dashboard_api/test_agent.py::test_agent_chat_endpoint_prompt_injection       PASSED
tests/dashboard_api/test_agent.py::test_agent_chat_endpoint_simulated_labels       PASSED

6 passed in 1.50s

---

## 12. Frontend Test Result

Test Files  10 passed (10)
Tests       45 passed (45)

---

## 13. Regression Guard

test_agent_chat_endpoint_is_registered_not_404 uses FastAPI TestClient (in-process).
This always loads current routes regardless of external server state, and will catch
any future case where the agent router is not registered in main.py.

---

## 14. Secondary Issue: HMR Hook Crash (Non-Bug)

The Vite dev server also crashed with:
  "Error: Rendered more hooks than during the previous render"
  Source: useSessionStatistics / useDemoOrchestrator in PipelinePage

Cause: React HMR artifact from a long-running dev server session (hours of hot reloads
accumulated stale fiber tree state). All hooks in these files are unconditional and
correctly ordered. The error does not occur on a fresh page load.

Fix: Restart Vite dev server. Does not recur.
