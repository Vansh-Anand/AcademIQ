# Phase E3: React Frontend Foundation and Application Shell

**Report Date:** 2026-08-30  
**Audit Status:** COMPLETE

## 1. Frontend Architecture
The frontend is structured in the `frontend/` directory with a standard Vite + React setup.
```text
frontend/
├── src/
│   ├── api/          # Centralized Axios client and typed domain API wrappers
│   ├── components/
│   │   ├── common/   # Reusable UI elements (badges, loaders, error states)
│   │   └── layout/   # AppShell layout including sidebar and top navigation
│   ├── pages/        # Route-level views (Overview, Pipeline, Evidence, etc.)
│   ├── tests/        # Vitest + React Testing Library unit tests
│   ├── types/        # TypeScript definitions mirroring the Phase E2 API contract
│   ├── App.tsx       # React Router setup
│   └── main.tsx      # Application entry point
├── vitest.config.ts  # Testing configuration
├── vite.config.ts    # Vite bundler configuration
└── tailwind.config.js
```

## 2. Technology Stack
- **React (via Vite):** Chosen for its lightweight footprint, fast HMR, and broad ecosystem.
- **TypeScript:** Enforces the API contract statically on the frontend to ensure data truthfulness.
- **Tailwind CSS v4:** Provides a clean, modern, minimal styling system without excessive abstraction or runtime overhead.
- **React Router v6:** Standard client-side routing.
- **Axios:** Selected for its robust interceptor support, built-in timeout configurations, and easy error formatting, critical for an API-heavy dashboard.
- **Lucide React:** Minimalist SVG icon set that aligns well with the cybersecurity aesthetic.
- **Vitest & React Testing Library:** Fast, native ES module testing mimicking a browser environment for high-confidence component validation.

## 3. API Integration
The frontend connects via a centralized `client.ts` Axios instance. Domain-specific modules (`pipeline.ts`, `evidence.ts`, `experiments.ts`) export strongly typed asynchronous functions (e.g., `runPipelineScenario`, `getEvidenceSessions`) mirroring the Phase E2 backend contract exactly.

## 4. Environment Configuration
The backend URL is configured via environment variables. The `frontend/.env.example` provides the default:
```env
VITE_API_BASE_URL=http://localhost:8000
```
This is loaded by Vite into `import.meta.env` and utilized by the Axios client to allow seamless swapping between local, staging, and production backends.

## 5. Execution Truthfulness System
The requirement to strictly distinguish execution modes is enforced natively through the `ExecutionModeBadge` component and statically typed across all API responses. It visually differentiates modes using color and explicit labels:
- **REAL_RUNTIME:** Emerald green (Indicates production or native physical layer execution)
- **SIMULATED:** Amber/Yellow (Indicates high-fidelity simulation but not native enforcement)
- **BENCHMARK:** Blue (Indicates controlled static benchmarking)
- **SYNTHETIC:** Purple (Indicates LLM-generated test data)
- **UNAVAILABLE:** Gray (Indicates component absence or inability to execute)

## 6. Routes Implemented
- `/` → **OverviewPage:** High-level dashboard summary showing L1-L7 availability.
- `/pipeline` → **PipelinePage:** Placeholder for the L1-L5 security scenario visualization.
- `/evidence` → **EvidencePage:** Placeholder for the ECES SQLite evidence chain browser.
- `/experiments` → **ExperimentsPage:** Placeholder for the benchmark and experiment chart results.
- `/system` → **SystemStatusPage:** Real-time diagnostics of API connection and backend health.

## 7. Components Created
- `AppShell.tsx`: The primary responsive layout wrapper with left navigation and top header.
- `ExecutionModeBadge.tsx`: Truthfulness indicator badge.
- `StatusBadge.tsx`: Reusable badge for pipeline decisions (ALLOW, BLOCK, WARN, etc.).
- `LoadingState.tsx`: Reusable spinner/loader.
- `ErrorState.tsx`: Structured API or component error box.
- `EmptyState.tsx`: Used for pending/unavailable features (e.g., placeholder pages).

## 8. Pages Created
- **OverviewPage.tsx:** Summarizes all 7 security layers, explicitly stating their operational status and execution mode limits (e.g., native eBPF on Windows marked explicitly as UNAVAILABLE).
- **PipelinePage.tsx:** Currently empty/placeholder for future detailed interactive visualizations.
- **EvidencePage.tsx:** Currently empty/placeholder for future chain validation.
- **ExperimentsPage.tsx:** Currently empty/placeholder for future metric plotting.
- **SystemStatusPage.tsx:** A live dashboard hitting `/api/health` to confirm orchestrator, SQLite, and experiment data accessibility.

## 9. Backend Connection Behavior
The `AppShell` runs a periodic (30-second interval) connectivity check against the API root/health endpoint.
- If connected, it renders an "API Connected" badge in the sidebar and normal routing occurs.
- If unavailable, the entire main content area is replaced by a "Backend Services Unavailable" blocking screen, preventing misleading empty states, while still allowing sidebar navigation.

## 10. Files Created
- `frontend/src/types/api.ts`
- `frontend/src/api/client.ts`, `pipeline.ts`, `evidence.ts`, `experiments.ts`
- `frontend/src/components/common/ExecutionModeBadge.tsx`, `StatusBadge.tsx`, `LoadingState.tsx`, `ErrorState.tsx`, `EmptyState.tsx`
- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/pages/OverviewPage.tsx`, `PipelinePage.tsx`, `EvidencePage.tsx`, `ExperimentsPage.tsx`, `SystemStatusPage.tsx`
- `frontend/src/App.tsx`, `main.tsx`, `index.css`, `vite.config.ts`, `vitest.config.ts`, `tests/setup.ts`, `tests/App.test.tsx`, `.env.example`

## 11. Files Modified
- (None outside the `frontend` directory; backend left entirely intact).

## 12. Dependencies Added
- `react`, `react-dom`
- `react-router-dom`: SPA client-side routing
- `tailwindcss`, `@tailwindcss/vite`: Utility-first CSS framework
- `axios`: API client
- `lucide-react`: SVG icon library
- `clsx`, `tailwind-merge`: CSS class merging utilities for reusable components
- `vitest`, `@testing-library/react`, `jsdom`: Testing suite

## 13. Tests Added
- `frontend/src/tests/App.test.tsx` includes DOM tests for rendering the correct styles in `ExecutionModeBadge` and `StatusBadge`, and verifying that the `AppShell` router correctly structures the application. 
- Coverage focuses on architectural correctness rather than granular unit behavior.

## 14. Build Result
- `npm run build` succeeds with zero TypeScript errors.
- `npm run test` executes successfully.

## 15. Known Limitations
- The Pipeline, Evidence, and Experiments pages are currently only structural placeholders using `EmptyState`.
- Complex charting libraries (e.g., Recharts) are not yet installed or integrated.
- Native eBPF visualization is hardcoded to show UNAVAILABLE on Windows environments as requested.

## 16. Frontend Readiness
The **frontend foundation is complete and ready** for Phase E4 (Detailed Security Pipeline Visualization). The backend contract is strictly enforced, and truthfulness mechanisms are globally integrated into the UI.
