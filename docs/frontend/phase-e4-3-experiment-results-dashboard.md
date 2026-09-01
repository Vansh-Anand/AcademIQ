# Phase E4.3: Experiment Results Dashboard

## Overview
Phase E4.3 focused on building an interactive, read-only visualization dashboard for AcademIQ's security research benchmarks. The project already contained extensive benchmark data scattered across heterogeneous JSON artifacts (`benchmarks/results/*`). This phase built the normalization layer and React frontend to browse and compare these results efficiently without compromising scientific integrity.

## Architecture

1. **Backend Normalization Layer (`dashboard_api/services/experiments_service.py`)**
   - Ingests `summary.json` files dynamically.
   - Handles schemas for core experiments (EXP-1 through EXP-5), real LLM variants, and patent techniques (Technique 1-5).
   - Maps divergent structures (e.g., lists of scenarios vs nested dicts) into a unified `ExperimentNormalized` Pydantic model.
   - Extracts baseline vs protected metrics for ASR, F1, Detection Rate, and Latency.

2. **Backend API Endpoints (`dashboard_api/routers/experiments.py`)**
   - `GET /api/experiments`: Returns lightweight summaries for the catalog view.
   - `GET /api/experiments/{id}`: Returns the full normalized detail, including raw JSON artifacts.

3. **Frontend Dashboard (`frontend/src/pages/ExperimentsPage.tsx`)**
   - **Catalog & Filters**: Allows filtering by dynamically extracted categories and execution modes (`REAL_RUNTIME`, `SYNTHETIC`, `BENCHMARK`, `SIMULATED`).
   - **Detail View**: Rich presentation of the selected experiment.
     - **Truthfulness Banners**: Contextual alerts (e.g., "REAL LLM INFERENCE" in emerald green) to visually differentiate data sources.
     - **Performance Grids**: Visualizes ASR drops and Detection Rate gains side-by-side using `BaselineComparison`.
     - **Raw Artifact Viewer**: A collapsible code block containing the original `summary.json` to ensure 100% transparency.
   - **Comparison Drawer**: A sticky bottom drawer that lets users select up to 3 experiments for a side-by-side metric comparison table.

## Data Integrity Constraints
- **Zero Fabrication**: If a metric is not present in the artifact, it is explicitly shown as "Unavailable" or "—". The dashboard does not fabricate `0`s for missing data.
- **Truthfulness-First**: The `execution_mode` flag is deeply integrated, guaranteeing that users instantly know whether metrics originated from synthetic simulated datasets or real LLM runtime evaluations.

## Future Phases
- Integrate WebSocket-based live telemetry.
- Connect the dashboard to real-time execution in Phase E5.
