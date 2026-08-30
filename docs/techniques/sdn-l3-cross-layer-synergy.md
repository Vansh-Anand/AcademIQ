# Technique 5: SDN → L3 Cross-Layer False Positive Reduction Measurement

## Objective
The objective of this technique is to formally measure whether semantic normalization provided by Layer 2 (Semantic Deobfuscation and Normalization - SDN) improves the accuracy of downstream Layer 3 (Execution Correlation Manager) by reducing false positives when correlating user space approvals with kernel space execution telemetry.

## Background
AcademIQ contains multiple defense layers:
- **Layer 2 (SDN):** Intercepts user commands, normalizes obfuscation, canonicalizes paths, and makes policy decisions before execution.
- **Layer 3 (eBPF Correlation):** Monitors actual kernel execution (`execve`, `ptrace`, `connect`) and correlates them back to L2 approvals within a small time window.

**The Problem:**
Without L2 canonicalization, L3 may receive raw command context from L2. When the OS kernel executes a command, it often normalizes paths (e.g., resolving `.` and `..`, removing quotes). If L3 naively compares the raw L2 string against the normalized OS syscall arguments, it may fail to correlate them, resulting in a **False Positive** (a benign command is blocked by L3 because it didn't strictly match the L2 approval).

**The Solution:**
By passing the **canonicalized** command string from L2 to L3, the correlation engine can perform accurate semantic matching, significantly reducing false positives.

## Experiment Methodology
To measure this synergy, an A/B benchmark experiment (`benchmarks/experiments/technique5_cross_layer_synergy.py`) was implemented with 6 carefully designed payload scenarios:

### Payloads:
1. **SCENARIO 1 (Plain Benign Command):** `cat /tmp/safe.txt`
2. **SCENARIO 2 (Benign Path Representation Variation):** `cat /tmp/././safe.txt`
3. **SCENARIO 3 (Benign Path Traversal Representation):** `cat /tmp/../tmp/safe.txt`
4. **SCENARIO 4 (Malicious Plain Command):** `rm -rf /etc/passwd`
5. **SCENARIO 5 (Malicious Obfuscated Command):** `r\m -r\f /etc/passwd`
6. **SCENARIO 6 (Authorization Correlation Mismatch):** `c'a't /t'm'p/safe.txt`

### Conditions:
- **Condition A (RAW_L3_ONLY):** Simulates L3 receiving raw, un-normalized command text from L2. L3 attempts to correlate the OS syscall against this raw string.
- **Condition B (SDN_NORMALIZED_L3):** L2 fully processes and canonicalizes the command before passing the resulting canonical string to L3 for correlation.

## Results
The benchmark results clearly demonstrate the synergy between L2 normalization and L3 correlation accuracy:

| Scenario | Ground Truth | RAW L3 Decision | NORMALIZED L3 Decision | Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **1** | BENIGN | ALLOW | ALLOW | Both succeed. |
| **2** | BENIGN | **BLOCK (FP)** | ALLOW | RAW fails to correlate due to `.` variations. |
| **3** | BENIGN | ALLOW | ALLOW | Both succeed (path traversal args accidentally match substring). |
| **4** | MALICIOUS | ALLOW (FN) | **BLOCK (TP)** | L2 blocks malicious activity before L3. |
| **5** | MALICIOUS | ALLOW (FN) | **BLOCK (TP)** | L2 blocks malicious activity before L3. |
| **6** | BENIGN | **BLOCK (FP)** | ALLOW | RAW fails to correlate due to severe quote obfuscation. |

### Metrics Summary:
- **RAW L3 False Positive Rate (FPR):** `50.00%` (Blocked benign scenarios 2 and 6)
- **NORMALIZED L3 False Positive Rate (FPR):** `0.00%` (Correctly allowed all benign scenarios)
- **False Positive Reduction:** `100.00%`

## Conclusion
The experiment formally validates that passing canonicalized command representations from L2 to L3 completely eliminates correlation mismatches caused by syntactic variations or obfuscation of benign commands. Semantic normalization is critical not just for policy enforcement at L2, but also for maintaining high-fidelity correlation accuracy at L3.
