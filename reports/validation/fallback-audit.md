# Fallback Audit

An audit of `try/except` and fallback logic across AcademIQ.

## 1. L6 ECES Hasher
- **Location**: `l6_eces/crypto/hasher.py`
- **Trigger**: `import blake3` failing.
- **Fallback**: `hashlib.sha256`
- **Security Consequence**: Uses slower standard hashing. 
- **Configured Behavior**: Records `"hash_algorithm": "SHA-256"` inside the `EvidenceRecord`. It explicitly DOES NOT claim BLAKE3 if it uses SHA-256.
- **Fail-open/Closed**: Closed (Valid cryptographic fallback).

## 2. L1 Grammar Parser
- **Location**: `l1_gcd/compiler.py`
- **Trigger**: Grammar syntax error.
- **Fallback**: Throws `GrammarCompilationError`
- **Security Consequence**: Model initialization halted.
- **Fail-open/Closed**: FAIL CLOSED.

## 3. L7 Detector
- **Location**: `l7_trust/detector.py`
- **Trigger**: Missing `/proc/cpuinfo` on Linux or Windows host.
- **Fallback**: All capabilities marked `False`.
- **Security Consequence**: HIGH_ASSURANCE boot halts.
- **Fail-open/Closed**: FAIL CLOSED.

## 4. L3 BPF Load
- **Location**: `orchestrator/health/manager.py`
- **Trigger**: FAILED status in any component.
- **Fallback**: In STANDARD mode, degrades. In HIGH_ASSURANCE, raises `RuntimeError` and HALTS system.
- **Fail-open/Closed**: FAIL CLOSED (in High-Assurance).

## Recommendation
No silent fail-open vulnerabilities were detected in critical enforcement code. The BPF fallback to simulated collector logs a `DEGRADED` health state but doesn't halt the system unless `HIGH_ASSURANCE` is active, which is correct by design.
