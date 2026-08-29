# AcademIQ Trust Boundaries

## Trust Levels

- **T0 (Untrusted Agent)**: The LLM process, executing in a heavily restricted cgroup/namespace. Cannot access security files or memory.
- **T1 (Host Kernel)**: The Linux Kernel, enforcing eBPF hooks and seccomp.
- **T2 (Security Monitor)**: The AcademIQ Orchestrator (L1-L5), running out-of-band. Evaluates telemetry and outputs ECES logs.
- **T3 (Hardware Trust Anchor)**: Intel TDX / AMD SEV-SNP and TPM backing the signing key and execution state.
- **T4 (Verified Remote Attestation)**: The external relying party that verifies the `AttestationEvidence` and the ECES chain signature.

## Boundaries and Transitions

1. **Agent ↔ Monitor Boundary**: 
   - *Crosses*: Telemetry (Syscalls via eBPF).
   - *Authentication*: Derived from Kernel `cgroup_id` (Spoof-resistant).
   - *Validation*: Unrecognized `cgroup_id` telemetry is dropped.
   
2. **Monitor ↔ TEE Boundary**:
   - *Crosses*: Security measurements, quote challenges.
   - *Authentication*: Nonce-based cryptographic binding.
   - *Validation*: Hardware signature validation by remote party.

3. **Monitor ↔ ECES Storage**:
   - *Crosses*: Append-only EvidenceRecords.
   - *Authentication*: Signed using TPM/Software signer.
   - *Validation*: Verified offline using `EvidenceVerifier`.

## Privilege Model

The agent process runs unprivileged without `CAP_BPF` or `CAP_SYS_ADMIN`. The Security Monitor requires `CAP_BPF` and `CAP_PERFMON` to load eBPF programs, but drops `CAP_SYS_ADMIN` after initialization.
