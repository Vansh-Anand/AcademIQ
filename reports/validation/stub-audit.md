# Stub & Mock Audit

The codebase was searched for stubs, NotImplementedErrors, and mocks.

| Location | Component | Type | Classification | Reason |
|----------|-----------|------|----------------|--------|
| `l3_ebpf/collector.py` | NativeEBpfCollector | `NotImplementedError` | UNIMPLEMENTED | Linux native headers required. Windows environment blocks direct compilation of eBPF objects. |
| `l6_eces/crypto/signer.py` | WindowsTPMSigner | `NotImplementedError` | UNIMPLEMENTED | Requires C++ CryptoAPI bindings not compiled in the env. |
| `l6_eces/crypto/signer.py` | LinuxTPMSigner | `NotImplementedError` | UNIMPLEMENTED | Requires `tpm2-tools` unavailable on Windows. |
| `l7_trust/tee/provider.py` | IntelTDXProvider | `NotImplementedError` | UNIMPLEMENTED | Intel TDX is a physical server feature; hardware is absent. |
| `l7_trust/tee/provider.py` | AMDSEVSNPProvider | `NotImplementedError` | UNIMPLEMENTED | SEV-SNP is a physical server feature; hardware is absent. |
| `tests/integration/*` | Multiple | Mocks | LEGITIMATE TEST MOCK | Used for deterministically mocking inputs rather than testing host functionality (e.g., L3 telemetry generation). |
| `l7_trust/tee/provider.py` | SimulationTEEProvider | Simulation logic | SIMULATION PROVIDER | Explicit fallback deterministic quotes for testing and development. |

## Conclusion
There are zero fake "stubs" inside production logic that claim to provide functionality but do not. The stubs present correctly `raise NotImplementedError` in classes representing hardware/native features not present in this Windows dev environment.
