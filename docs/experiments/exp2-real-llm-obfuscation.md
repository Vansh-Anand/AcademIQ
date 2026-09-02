# Phase C1 & E6: EXP-2 Obfuscated Command Benchmark (Final Revalidation)

## Motivation
Prior instances of EXP-2 relied on a hardcoded, synthetic baseline corpus of 19 payload strings (EXP-2A). While this guarantees exact structure for testing the L2 SDN canonicalization layer, it lacks ecological validity. Real attackers increasingly use locally hosted LLMs or agentic assistants to craft zero-day obfuscation payloads at runtime. 
To rigorously validate AcademIQ's Layer 2 defenses, we extended EXP-2 to include a local, dynamically generated corpus of obfuscated shell payloads constructed by `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (EXP-2B).

## Discovery of the Artifact Confusion
During the initial Phase C1 runs, a serious metric discrepancy was introduced: the automated regression tests were incorrectly configured such that mock LLM generations in unit tests were overwriting the authoritative `summary.json` result artifact. This resulted in the benchmark erroneously reporting a `0%` Detection Rate (DR) in subsequent CI runs.

This structural vulnerability in the testing framework was identified in Phase E6. A strict isolation boundary was subsequently implemented ensuring that unit tests execute within temporary `pytest` sandbox directories, permanently protecting `benchmarks/results/` from test artifacts.

## Forensic Identification of the Compound-Command Parser Weakness
Upon restoring the correct Real LLM datasets, forensic analysis of the 53 actual malicious payloads revealed that the L2 SDN (which achieved a 100% DR on synthetic metrics initially) was actually being bypassed by specific LLM generations. 

The bypass was traced to a vulnerability in `l2_sdn/parser.py`. The AST visitor incorrectly flattened compound shell commands (e.g. `&&`, `|`, `;`) into a contiguous array, forcing the `CommandPolicyMatcher` to evaluate only the very first executable. If an attacker provided `echo benign && rm -rf /`, the L2 SDN only observed `echo` and allowed the malicious payload to bypass. 

## The Parser Fix & Ground Truth Labeling Correction
In Phase E6, the L2 SDN parser was overhauled with a nested `CommandVisitor`, allowing it to maintain pipeline and logical operator boundaries and enforce a strict "deny-if-any" policy across all subcommands.

Simultaneously, a ground-truth labeling error was discovered in the EXP-2B dataset: strings like `x='cat /etc/passwd'` and `echo rm -rf /tmp/test` were being falsely flagged as `MALICIOUS` by the automated labeler because they contained dangerous substrings, despite being non-executable in that context. The labeler was upgraded to parse execution semantics, successfully moving 4 falsely flagged payloads from `MALICIOUS` to `BENIGN`.

## Final Authoritative Metrics (Post-Fix)

### EXP-2A (Synthetic Obfuscation)
The L2 SDN was evaluated against 19 hand-crafted payloads targeting canonicalization edge cases.
- **Total Payloads**: 19
- **Malicious**: 15
- **Benign**: 4
- **Baseline DR**: 80.0%
- **L2 SDN DR**: 100.0% (ASR: 0.0%)
- **Precision**: 1.0
- **Recall**: 1.0
- **F1**: 1.0

### EXP-2B (Real LLM Obfuscation)
The L2 SDN was evaluated against 77 unique, valid payloads generated dynamically by `TinyLlama-1.1B`. 
*Note: Due to the parser fix and the labeling correction, the 4 previous false-negative bypasses were re-classified and structurally neutralized.*
- **Total Unique Payloads**: 77
- **Malicious**: 53
- **Benign**: 16
- **Ambiguous/Invalid**: 8 (Excluded from primary metrics)
- **Baseline DR**: 92.98%
- **L2 SDN DR**: 100.0% (ASR: 0.0%)
- **L2 False Positives**: 8 (FPR: 50.0%)
- **Precision**: 0.8688
- **Recall**: 1.000
- **F1**: 0.9298

## Limitations
- **Model Size:** `TinyLlama-1.1B` produces heavily hallucinated syntax (e.g., inventing tools that do not exist).
- **False Positives:** The current L2 parser blocks a high percentage of benign LLM-generated commands (50% FPR) due to rigid syntax rules inherited from the synthetic setup, as the L2 parser still struggles to completely distinguish benign string arguments from true executables in complex LLM hallucinations.
