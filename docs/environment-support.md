# AcademIQ Environment Support

## Target Architecture vs Current Host

AcademIQ is designed to operate on a modern Linux kernel with eBPF, `perf_event_open`, and Hardware-backed Trusted Execution Environments (TEEs) such as Intel TDX or AMD SEV-SNP.

This document describes the environment discovered during the Phase 1 implementation and details how AcademIQ gracefully handles these constraints using its Simulation Mode.

### Discovered Host Environment

- **Operating System:** Windows NT 10.0.26200.0
- **Python Version:** Python 3.13.6
- **Docker:** Available (Docker Desktop running on WSL 2)
- **Compiler:** Clang/LLVM not found in PATH natively
- **TPM:** Detected (TpmPresent=True) but not configured for native Linux `tpm2-tools` interaction
- **eBPF (libbpf, bpftool, BPF filesystem):** Unavailable (Windows host)
- **Hardware Telemetry (`perf_event_open`):** Unavailable (Windows host)

### Security Limitations on Current Host

1.  **L3 (eBPF Telemetry):** Because the host is Windows, we cannot insert eBPF kernel probes. The `NullEBPFProvider` or `SimulationEBPFProvider` must be used.
2.  **H3 (Hardware Telemetry):** CPU performance counters are not accessible natively via Linux `perf_event`. Synthetic metrics will be generated in Simulation Mode.
3.  **H1 (TEE):** Without a Linux host supporting TDX/SEV-SNP, attestation and memory encryption are mocked via the `SimulationTEEProvider`.
4.  **H2 (TOCTOU):** Inode bindings and Linux-specific path metadata (like `mtime_ns` combined with `device_id`) will use Windows equivalents or fallback to strings where precise filesystem identities cannot be guaranteed.

> [!WARNING]
> Running AcademIQ on this environment provides **NO ACTUAL SECURITY**. It is exclusively for interface testing, schema validation, and developing the higher-level logic (RiskChain, Governance, GCD) before deploying to the target Linux architecture.

### Simulation Mode

To develop on this machine, AcademIQ must be run with:

```bash
ACADEMIQ_MODE=simulation academiq run
```

Or by setting `development.simulation_mode = true` in `academiq.yaml`.

This explicitly instructs the orchestrator to load mock providers. Any events generated will have `simulation=true` in their schema.

### Target Deployment Requirements

For full security enforcement, the target environment must possess:

- Linux Kernel 5.15+ (with BTF enabled)
- Clang/LLVM 10+
- `libbpf` and `bpftool`
- `perf_event_open` privileges
- TPM 2.0 and `tpm2-tools`
- (Optional) Intel TDX or AMD SEV-SNP for confidential computing.
