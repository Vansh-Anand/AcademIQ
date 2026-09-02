# Experiment Metric Reconciliation Report

This document reconciles all historically reported metrics with the current canonical source of truth.

| Experiment | Historical Claim | Canonical Claim | Reason | Source of Truth | Status |
|---|---|---|---|---|---|
| EXP-1 | N=5 sample size | N=140 sample size | N=5 was an early pilot test. The expanded Phase A1 validation reliably evaluated N=140. | `benchmarks/results/exp1/summary.json` | RESOLVED |
| EXP-2B | 0% DR / 100% ASR | 100% DR / 0% ASR | Early 0% DR was a confirmed vulnerability due to a string flattening bug in the compound command parser. Revalidated after patch in Phase C1. | `benchmarks/results/exp2_real_llm/summary.json` | RESOLVED |
| EXP-2B | False Positives undefined | FPR = 50.0% | There were 8 false positives among 16 true benign extracted commands. 8/16 = 0.50. | `benchmarks/results/exp2_real_llm/summary.json` | RESOLVED |
| EXP-3_REAL_LLM | 100% end-to-end success | N=2 valid remaining after mock overwrite. Limitation: Only 18 usable typically produced from 55. | Test runner originally overwrote results. Only N=2 mock results were left in the result dir. The 55 generations generated many Throttle warnings rather than block. | `benchmarks/experiments/exp3_real_llm_exfiltration.py` | RESOLVED |
| EXP-4 / EXP-5 | EXP-4 described as Siamese + IF ensemble | EXP-5 is Siamese + IF; EXP-4 is Ptrace | Previous documentation conflated the labels. Canonical numbering separates EXP-4 (ptrace behavior) and EXP-5 (behavioral divergence model). | `Experiment scripts numbering` | RESOLVED |
| EXP-5 | 0% FPR | 0.5% FPR standalone | 0% FPR applies to the system when Technique 5 (SDN-L3 Cross-Layer Reduction) is active. The raw L4 standalone FPR is 0.5% (1/200). | `benchmarks/results/exp5/summary.json` | RESOLVED |
| EXP-6 | AARM Comparator | AARM-Inspired Baseline / Prior-Art Approximation | Scientific integrity requires clarifying that the test evaluates against an internal representation, not a true copy of the AARM codebase. | `benchmarks/experiments/exp6_aarm_comparison.py` | RESOLVED |
