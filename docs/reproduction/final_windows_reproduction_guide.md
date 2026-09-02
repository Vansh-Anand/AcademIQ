# Final Windows Reproduction Guide

This document guarantees reproducibility for the Windows-side execution of AcademIQ. It catalogs the exact commands required to rerun the entire pipeline, including all experiments, dashboard servers, and validation suites.

## 1. Full Python Regression Suite
- **Command:** `python -m pytest tests/ -v`
- **Expected Output Location:** Terminal (`STDOUT`).
- **Model Download Required:** No (uses mocked fixtures).
- **Approximate Runtime:** ~25 seconds.
- **Execution Mode:** SYNTHETIC / SIMULATED_EVENTS.
- **Platform Requirement:** Any OS (Windows / Linux).

## 2. Frontend Tests
- **Command:** `cd frontend && npm run test`
- **Expected Output Location:** Terminal (`STDOUT`).
- **Model Download Required:** No.
- **Approximate Runtime:** ~5 seconds.
- **Execution Mode:** N/A (Unit tests).
- **Platform Requirement:** Node.js installed.

## 3. Frontend Production Build
- **Command:** `cd frontend && npm run build`
- **Expected Output Location:** `frontend/dist/`.
- **Model Download Required:** No.
- **Approximate Runtime:** ~5 seconds.
- **Execution Mode:** N/A (Build step).
- **Platform Requirement:** Node.js installed.

## 4. EXP-1: Direct Prompt Injection
- **Command (TinyLlama):** `python benchmarks/experiments/exp1_direct_injection.py`
- **Command (Qwen2.5):** `python benchmarks/experiments/exp1_direct_injection_cross_model.py`
- **Expected Output Location:** `benchmarks/results/exp1/summary.json` and `benchmarks/results/exp1_cross_model/summary.json`
- **Model Download Required:** Yes (HuggingFace cache, ~4-6 GB each).
- **Approximate Runtime:** ~90 minutes (TinyLlama), ~100 minutes (Qwen2.5).
- **Execution Mode:** REAL_LLM_INFERENCE.
- **Platform Requirement:** Multi-core CPU / GPU.

## 5. EXP-2A: Synthetic Shell Obfuscation
- **Command:** `python benchmarks/experiments/exp2_shell_obfuscation.py`
- **Expected Output Location:** `benchmarks/results/exp2/summary.json`
- **Model Download Required:** No.
- **Approximate Runtime:** ~1 second.
- **Execution Mode:** SYNTHETIC.
- **Platform Requirement:** Any.

## 6. EXP-2B: Real LLM Obfuscation
- **Command:** `python benchmarks/experiments/exp2_shell_obfuscation_real_llm.py`
- **Expected Output Location:** `benchmarks/results/exp2_real_llm/summary.json`
- **Model Download Required:** Yes (TinyLlama).
- **Approximate Runtime:** ~10-15 minutes.
- **Execution Mode:** REAL_LLM_INFERENCE.
- **Platform Requirement:** Any.

## 7. EXP-3: Base Synthetic RiskChain Correlation
- **Command:** `python benchmarks/experiments/exp3_multistep_exfiltration.py`
- **Expected Output Location:** `benchmarks/results/exp3/summary.json`
- **Model Download Required:** No.
- **Approximate Runtime:** ~2 seconds.
- **Execution Mode:** SYNTHETIC.
- **Platform Requirement:** Any.

## 8. EXP-3: Real LLM Correlation
- **Command:** `python benchmarks/experiments/exp3_multistep_exfiltration_real_llm.py`
- **Expected Output Location:** `benchmarks/results/exp3_real_llm/summary.json`
- **Model Download Required:** Yes (TinyLlama).
- **Approximate Runtime:** ~5 minutes.
- **Execution Mode:** REAL_LLM_INFERENCE.
- **Platform Requirement:** Any.

## 9. EXP-4: Behavioral Divergence (L4)
- **Command:** `python benchmarks/experiments/exp4_divergence.py`
- **Expected Output Location:** `benchmarks/results/exp4/summary.json`
- **Model Download Required:** No.
- **Approximate Runtime:** ~1 second.
- **Execution Mode:** SIMULATED_EVENTS.
- **Platform Requirement:** Any.

## 10. EXP-5: Cross-Layer Synergy (L3)
- **Command:** `python benchmarks/experiments/exp5_cross_layer_synergy.py`
- **Expected Output Location:** `benchmarks/results/exp5/summary.json`
- **Model Download Required:** No.
- **Approximate Runtime:** ~2 seconds.
- **Execution Mode:** SIMULATED_EVENTS (synthesizes L3 telemetry).
- **Platform Requirement:** Any.

## 11. EXP-6: AARM Baseline Comparison
- **Command:** `python benchmarks/experiments/exp6_aarm_comparison.py`
- **Expected Output Location:** `benchmarks/results/exp6_aarm_comparison/summary.json`
- **Model Download Required:** No.
- **Approximate Runtime:** ~2 seconds.
- **Execution Mode:** SIMULATED_EVENTS.
- **Platform Requirement:** Any.

## 12. Dashboard Backend Startup
- **Command:** `uvicorn dashboard_api.main:app --reload --port 8000`
- **Expected Output Location:** `http://localhost:8000/docs`
- **Model Download Required:** No.
- **Approximate Runtime:** Continuous.
- **Execution Mode:** SERVER.
- **Platform Requirement:** Any.

## 13. Dashboard Frontend Startup
- **Command:** `cd frontend && npm run dev`
- **Expected Output Location:** `http://localhost:5173`
- **Model Download Required:** No.
- **Approximate Runtime:** Continuous.
- **Execution Mode:** SERVER.
- **Platform Requirement:** Any.

## 14. ECES Chain Verification
- **Command (Interactive API):** Make a GET request to `http://localhost:8000/evidence/verify/{session_id}`
- **Command (Via Script):** `python -m pytest tests/integration/test_l6_eces.py -k test_chain_creation_and_verification`
- **Expected Output Location:** JSON Response / Pytest Output.
- **Model Download Required:** No.
- **Approximate Runtime:** ~0.1 seconds.
- **Execution Mode:** CRYPTOGRAPHIC VALIDATION.
- **Platform Requirement:** Any.
