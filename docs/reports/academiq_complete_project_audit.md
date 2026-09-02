# AcademIQ Master Project Audit (Canonical Edition)
> [!IMPORTANT]
> This is the canonical, auto-generated audit report sourced from `experiment_registry.json`.
> The historical audit report has been preserved as `historical_academiq_project_audit.md`.

## 1. Project Status
- **Overall Status:** FROZEN STATE (Pre-Ubuntu Handoff).
- **Windows Validation:** Complete. All 145 Python regression tests pass.
- **Native Ubuntu/eBPF Status:** PENDING / NOT VALIDATED. (Do not start Ubuntu work yet).
- **Dashboard Status:** React + FastAPI dashboard fully implemented and tested.
- **ECES Status:** Durable SQLite storage implemented.
- **Phase 4 Technique Status:** All five patent-strengthening techniques implemented and validated.

## 2. Canonical Experiment Table
| ID | Title | Mode | Dataset | Samples | Malicious | DR (%) | ASR (%) | FPR (%) |
|---|---|---|---|---|---|---|---|---|
| EXP-1 | Direct Prompt Injection | REAL_RUNTIME | REAL_LLM | 140 | 120 | 100.0 | 0.0 | 53.3 |
| EXP-2A | Obfuscated Command Detection (Synthetic) | SYNTHETIC | SYNTHETIC | 19 | 15 | 100.0 | 0.0 | 0.0 |
| EXP-2B | Obfuscated Command Detection (Real LLM) | REAL_RUNTIME | REAL_LLM | 77 | 53 | 100.0 | 0.0 | 50.0 |
| EXP-3 | Multi-Step Exfiltration (Synthetic) | SYNTHETIC | SYNTHETIC | 6 | 1 | 100.0 | 0.0 | 100.0 |
| EXP-3_REAL_LLM | Multi-Step Exfiltration (Real LLM) | REAL_RUNTIME | REAL_LLM | 2 | 1 | 100.0 | 0.0 | 0.0 |
| EXP-4 | Ptrace-Like Process Manipulation Detection | SYNTHETIC | SYNTHETIC | 3 | 1 | 100.0 | 0.0 | 0.0 |
| EXP-5 | Behavioral Divergence (Siamese + Isolation Forest) | SIMULATED | SYNTHETIC | 400 | 200 | 100.0 | 0.0 | 0.5 |
| EXP-6 | AARM-Inspired Baseline vs AcademIQ | SIMULATED | SYNTHETIC | 6 | 5 | 100.0 | 0.0 | 0.0 |

## 3. Experiment-by-Experiment Results
### EXP-1: Direct Prompt Injection
- **Status:** AUTHORITATIVE
- **Execution Mode:** REAL_RUNTIME
- **Dataset Type:** REAL_LLM
- **Detection Rate:** 100.0%
- **Attack Success Rate:** 0.0%
- **False Positive Rate:** 53.333333333333336%
- **Samples:** 140 total (120 malicious, 20 benign)
- **Mean Latency:** 4787.01 ms
- **Notes:**
  - N=5 was an early pilot. The canonical expanded experiment used N=140 with TinyLlama.

### EXP-2A: Obfuscated Command Detection (Synthetic)
- **Status:** AUTHORITATIVE
- **Execution Mode:** SYNTHETIC
- **Dataset Type:** SYNTHETIC
- **Detection Rate:** 100.0%
- **Attack Success Rate:** 0.0%
- **False Positive Rate:** 0.0%
- **Samples:** 19 total (15 malicious, 4 benign)
- **Mean Latency:** 13.14 ms
- **Notes:**
  - Result reflects revalidation after Phase C1 parser fix.

### EXP-2B: Obfuscated Command Detection (Real LLM)
- **Status:** AUTHORITATIVE
- **Execution Mode:** REAL_RUNTIME
- **Dataset Type:** REAL_LLM
- **Detection Rate:** 100.0%
- **Attack Success Rate:** 0.0%
- **False Positive Rate:** 50.0%
- **Samples:** 77 total (53 malicious, 16 benign)
- **Mean Latency:** 43.24 ms
- **Notes:**
  - Result reflects revalidation after Phase C1 parser fix.
  - FPR is 8 FP / 16 benign = 50%.

### EXP-3: Multi-Step Exfiltration (Synthetic)
- **Status:** AUTHORITATIVE
- **Execution Mode:** SYNTHETIC
- **Dataset Type:** SYNTHETIC
- **Detection Rate:** 100.0%
- **Attack Success Rate:** 0.0%
- **False Positive Rate:** 100.0%
- **Samples:** 6 total (1 malicious, 5 benign)
- **Mean Latency:** 533.20 ms

### EXP-3_REAL_LLM: Multi-Step Exfiltration (Real LLM)
- **Status:** AUTHORITATIVE
- **Execution Mode:** REAL_RUNTIME
- **Dataset Type:** REAL_LLM
- **Detection Rate:** 100.0%
- **Attack Success Rate:** 0.0%
- **False Positive Rate:** 0.0%
- **Samples:** 2 total (1 malicious, 1 benign)
- **Mean Latency:** 117.50 ms
- **Notes:**
  - Test overwrote this summary file prior to audit. The restored numbers reflect only 2 valid sequences remaining from the mock overwrite.
- **Limitations:**
  - Original experiment targeted 55 generations (11 prompts x 5 seeds). Only 18 unique usable sequences were typically produced.
  - High rate of throttling due to L5 RiskChain before explicit divergence.

### EXP-4: Ptrace-Like Process Manipulation Detection
- **Status:** AUTHORITATIVE
- **Execution Mode:** SYNTHETIC
- **Dataset Type:** SYNTHETIC
- **Detection Rate:** 100.0%
- **Attack Success Rate:** 0.0%
- **False Positive Rate:** 0.0%
- **Samples:** 3 total (1 malicious, 2 benign)
- **Mean Latency:** 35.18 ms

### EXP-5: Behavioral Divergence (Siamese + Isolation Forest)
- **Status:** AUTHORITATIVE
- **Execution Mode:** SIMULATED
- **Dataset Type:** SYNTHETIC
- **Detection Rate:** 100.0%
- **Attack Success Rate:** 0.0%
- **False Positive Rate:** 0.5%
- **Samples:** 400 total (200 malicious, 200 benign)
- **Mean Latency:** 3.18 ms
- **Notes:**
  - Standalone FPR is 0.5%. Reduced to 0.0% by Technique 5 (SDN-L3 Cross-Layer synergy).
- **Limitations:**
  - Simulation-based payload data, not real runtime.

### EXP-6: AARM-Inspired Baseline vs AcademIQ
- **Status:** AUTHORITATIVE
- **Execution Mode:** SIMULATED
- **Dataset Type:** SYNTHETIC
- **Detection Rate:** 100.0%
- **Attack Success Rate:** 0.0%
- **False Positive Rate:** 0.0%
- **Samples:** 6 total (5 malicious, 1 benign)
- **Limitations:**
  - AARMEquivalentDetector is an internal approximation and not an official reproduction.
  - AcademIQ is a multi-layer architecture while the baseline intentionally evaluates isolated semantic actions.
  - Sample sizes are extremely small (1 per category).

## 4. Historical Discrepancies
This table reconciles historically reported metrics with the current canonical source of truth.

| Experiment | Historical Claim | Canonical Claim | Reason | Source of Truth |
|---|---|---|---|---|
| EXP-1 | N=5 sample size | N=140 sample size | N=5 was an early pilot test. The expanded Phase A1 validation reliably evaluated N=140. | `benchmarks/results/exp1/summary.json` |
| EXP-2B | 0% DR / 100% ASR | 100% DR / 0% ASR | Early 0% DR was a confirmed vulnerability due to a string flattening bug in the compound command parser. Revalidated after patch in Phase C1. | `benchmarks/results/exp2_real_llm/summary.json` |
| EXP-2B | False Positives undefined | FPR = 50.0% | There were 8 false positives among 16 true benign extracted commands. 8/16 = 0.50. | `benchmarks/results/exp2_real_llm/summary.json` |
| EXP-3_REAL_LLM | 100% end-to-end success | N=2 valid remaining after mock overwrite. Limitation: Only 18 usable typically produced from 55. | Test runner originally overwrote results. Only N=2 mock results were left in the result dir. The 55 generations generated many Throttle warnings rather than block. | `benchmarks/experiments/exp3_real_llm_exfiltration.py` |
| EXP-4 / EXP-5 | EXP-4 described as Siamese + IF ensemble | EXP-5 is Siamese + IF; EXP-4 is Ptrace | Previous documentation conflated the labels. Canonical numbering separates EXP-4 (ptrace behavior) and EXP-5 (behavioral divergence model). | `Experiment scripts numbering` |
| EXP-5 | 0% FPR | 0.5% FPR standalone | 0% FPR applies to the system when Technique 5 (SDN-L3 Cross-Layer Reduction) is active. The raw L4 standalone FPR is 0.5% (1/200). | `benchmarks/results/exp5/summary.json` |
| EXP-6 | AARM Comparator | AARM-Inspired Baseline / Prior-Art Approximation | Scientific integrity requires clarifying that the test evaluates against an internal representation, not a true copy of the AARM codebase. | `benchmarks/experiments/exp6_aarm_comparison.py` |

## 5. Known Limitations & Strict Rules
- **EXP-6 Comparator Limitation:** The AARMEquivalentDetector is an internal AARM-inspired baseline / prior-art approximation benchmark, NOT the actual AARM system.
- **Real vs Simulated:** Synthetic and simulated results are strictly labeled and are not claimed to be real-world results.
- **Native OS Validation:** L7 native OS isolation and native eBPF validation are not yet claimed. They will be validated in the subsequent Ubuntu phase.

## 6. Git/Repository Hygiene Findings
- **`__pycache__`:** Tracked in git (Recommended: Untrack).
- **`eces.db`:** Tracked in git (Recommended: Untrack).
- **`l4_siamese.pt`:** Tracked in git (Acceptable size).
- **Secrets/node_modules:** None tracked.
