# AcademIQ Demo Walkthrough

This document provides a guided walkthrough for demonstrating the full end-to-end capabilities of the AcademIQ dashboard and backend security architecture.

## Pre-requisites

Ensure both the backend API and the frontend are running:
1. **Backend**: `uvicorn dashboard_api.main:app --reload --port 8000`
2. **Frontend**: `cd frontend && npm run dev`

Navigate to `http://localhost:5173` in your browser.

## Step 1: The Overview Dashboard
**URL**: `/`

- Explain the architecture of the dashboard: It integrates seamlessly with the backend simulation.
- Point out the **Security Infrastructure Health** section: Note that the "eBPF Agent" is marked as `UNAVAILABLE` on Windows, demonstrating our commitment to scientific honesty.
- Review the dynamically loaded active sessions, recent events, and evidence chains.
- Note the **System Execution Mode**: It correctly reflects `SIMULATION`.

## Step 2: Live Security Pipeline
**URL**: `/pipeline`

- Initiate a **Safe Read** scenario:
  - Watch the pipeline execute layer by layer.
  - See L1 (Grammar-Constrained Decoding) and L2 (Semantic Deobfuscation) explicitly allow the event.
  - Review the 0.1 divergence score from L4 (Siamese Recurrent Autoencoder).
  - Observe the overall `ALLOW` decision.
- Initiate an **Obfuscated Command** attack scenario:
  - See the exact layer (L1 GCD) block the payload `execute_shell("")` before generation even occurs.
  - Observe the overall `BLOCK` decision and the generation of an ECES hash chain for auditability.

## Step 3: ECES Audit Chain Inspector
**URL**: `/evidence`

- Click on the session ID of the attack you just ran.
- View the **Cryptographic Evidence Chain**:
  - Show the `genesis` block initialized for the session.
  - Show the blocked `ToolInvocation` event safely stored in the append-only ledger.
  - Show the final `Enforcement` action taken by the system.
- Click **Verify Chain Signature**:
  - Prove that the cryptographic hashes match correctly and the sequence numbers are intact, demonstrating tamper-evident logging.

## Step 4: Research Benchmarks
**URL**: `/experiments`

- Navigate through the completed experiment benchmarking datasets.
- Highlight **EXP-1**: The Siamese Recurrent Autoencoder performance demonstrating 99.4% F1-score across syscall traces.
- Note that all charts clearly label their data as `SYNTHETIC` or `REAL_RUNTIME` depending on the experiment configuration.

## Step 5: System Status
**URL**: `/status`

- Show the live health checks confirming connection to SQLite and the active Mock TEE.
- Conclude the demo by emphasizing the transparent, zero-trust nature of the AcademIQ platform.
