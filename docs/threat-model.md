# AcademIQ Threat Model

## Trust Zones

- **ZONE A:** Untrusted external/user input.
- **ZONE B:** Autonomous LLM agent.
- **ZONE C:** Tool execution/runtime.
- **ZONE D:** Host kernel.
- **ZONE E:** AcademIQ security infrastructure.
- **ZONE F:** Hardware-backed security (TPM, TEE, performance counters).
- **ZONE G:** Forensic evidence storage.

## Identified Threats

| Threat | Description | Relevant Layer | Detection/Prevention Mechanism | Residual Risk | Status |
|---|---|---|---|---|---|
| **T1** | Prompt injection | L1 GCD | Grammar restriction limits syntax | Bypass via valid grammar | PLANNED |
| **T2** | Indirect prompt injection | L1 GCD | Same as above | Bypass via valid grammar | PLANNED |
| **T3** | Malicious tool-call generation | L1 GCD | Masking before softmax | Zero-day LLM evasion | PLANNED |
| **T4** | Shell command obfuscation | L2 SDN | Five-pass deobfuscation | Unmodeled obfuscation | PLANNED |
| **T5** | Base64/hex/octal/ANSI-C evasion | L2 SDN | Canonicalization | Extreme nested encoding | PLANNED |
| **T6** | Alias/function-based evasion | L2 SDN | Policy enforcement | Dynamic resolution | PLANNED |
| **T7** | Path traversal | L2 SDN | Path metadata resolution | Complex symlinks | PLANNED |
| **T8** | Symlink substitution | L2 SDN / TOCTOU | Inode/Device binding | Kernel race conditions | PLANNED |
| **T9** | TOCTOU race | L2 SDN / TOCTOU | Immutable path identity | Extreme timing | PLANNED |
| **T10** | Malicious file replacement | L2 / L4 | Divergence engine | Unknown | PLANNED |
| **T11** | Syscall sequence mimicry | L4 / L3 | Isolation Forest / Siamese | Mimicry attacks | PLANNED |
| **T12** | Behavioral zero-day | L4 / L5 | RiskChain | High false positive | PLANNED |
| **T13** | Multi-step exfiltration | L5 RiskChain | Temporal graph correlation | Slow-drip exfiltration | PLANNED |
| **T14** | Monitoring discovery | L3 eBPF | Host-only eBPF, invisible to container | Root compromise | PLANNED |
| **T15** | Container escape attempts | L3 eBPF | Namespace enforcement | Kernel exploits | PLANNED |
| **T16** | Telemetry tampering | L3 / F | hardware counters | TEE bypass | PLANNED |
| **T17** | Audit-log tampering | L5 ECES | Append-only hash chain | Disk destruction | PLANNED |
| **T18** | Key extraction attempts | F / TEE | Hardware sealing | Side-channel attacks | PLANNED |
| **T19** | Compromised host | F / TEE | Intel TDX / SEV-SNP | Hypervisor attacks | PLANNED |
| **T20** | Hardware-perf mimicry | H3 | perf_event signature matching | Complex stalling | PLANNED |
| **T21** | Security-engine compromise | F / TEE | TEE isolation | TEE vulnerability | PLANNED |
| **T22** | False positives | L5 | Governance & ECE | Usability impact | PLANNED |
| **T23** | DoS against security | L1-L5 | Rate limiting & Throttle | Resource exhaustion | PLANNED |
