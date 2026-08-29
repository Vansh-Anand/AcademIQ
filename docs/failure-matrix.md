# AcademIQ Failure Matrix

This matrix maps component failures to the fail-safe behavior in STANDARD and HIGH_ASSURANCE modes.

| Component | Failure Mode | Standard Behavior | High-Assurance Behavior | ECES Record |
|-----------|-------------|--------------------|-------------------------|-------------|
| **L1** (GCD) | Grammar parsing exception | Disallow generation (FAIL CLOSE) | Disallow generation (FAIL CLOSE) | L1_REJECT |
| **L2** (SDN) | Obfuscation analysis timeout | Assume obfuscated (FAIL CLOSE) | Assume obfuscated (FAIL CLOSE) | L2_REJECT |
| **L3** (eBPF) | Collector crash / Map lost | Alert and Degrade | HALT System | DEGRADATION_EVENT |
| **L4** (Div) | Inference failure / Timeout | Ignore (DEGRADE) | Ignore (DEGRADE) | DEGRADATION_EVENT |
| **L5** (Risk) | Governance exception | FREEZE Agent | FREEZE Agent | L5_FREEZE |
| **ECES** | Storage full / Write error | Log locally, continue | HALT System | DEGRADATION_EVENT |
| **TPM** | Signing interface down | Fallback Software | HALT System | DEGRADATION_EVENT |
| **TEE** | Attestation Quote failure | Warn | HALT System | DEGRADATION_EVENT |

### No Silent Fail-Open
AcademIQ guarantees that any failure in a required enforcement boundary (L1, L2, L5) strictly fails *closed*. Hardware root-of-trust failures (TPM/TEE) fail closed in `HIGH_ASSURANCE` mode.
