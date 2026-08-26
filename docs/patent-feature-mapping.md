# Patent Feature Mapping

This document maps planned AcademIQ implementations to required patent features.

| Patent Feature | Layer | Technical Mechanism | Implementation Module | Validation | Status |
|---|---|---|---|---|---|
| PDA-based security-policy constrained decoding | L1 | CFG -> PDA Automaton | `l1_gcd.automaton` | Adversarial | IMPLEMENTED |
| Token masking before softmax | L1 | Logits mutation | `l1_gcd.masking` | Benchmark | TESTED |
| Five-pass shell normalization | L2 | AST traversal | `l2_sdn.normalizers` | Adversarial | TESTED |
| Variable expansion | L2 | Regex substitution | `l2_sdn.normalizers` | Adversarial | TESTED |
| Encoding decoding | L2 | Base64/Hex/Octal | `l2_sdn.normalizers` | Adversarial | TESTED |
| ANSI-C normalization | L2 | Bashlex + Regex | `l2_sdn.normalizers` | Adversarial | TESTED |
| Alias/function resolution | L2 | Dictionary lookup | `l2_sdn.normalizers` | Adversarial | TESTED |
| Command canonicalization | L2 | AST transformation | `l2_sdn.canonicalizer` | Adversarial | TESTED |
| Policy trie matching | L2 | Trie/List logic | `l2_sdn.policy.matcher` | Adversarial | TESTED |
| TOCTOU-resistant path identity | L2 | Inode tracking | `l2_sdn.toctou.resolver` | Unit Test | TESTED |
| Symlink replacement detection | L2 | Identity checking | `l2_sdn.toctou.verifier` | Unit Test | TESTED |
| Fail-closed unresolved execution | L2 | Strict mode | `l2_sdn.interceptor` | Adversarial | TESTED |
| L2 event generation | L2 | `NormalizedCommandEvent` | `l2_sdn.events` | System Test | IMPLEMENTED |
| Host-only eBPF telemetry | L3 | libbpf / uprobe | `l3_ebpf.probes` | Integration | SCAFFOLDED |
| Namespace-based monitoring invisibility | L3 | cgroup/ns filtering | `l3_ebpf.namespace` | Security | SCAFFOLDED |
| Pure syscall topology | L3 | syscall sequence | `l3_ebpf.kernel` | Integration | SCAFFOLDED |
| Siamese recurrent autoencoder | L4 | PyTorch LSTM | `l4_divergence.siamese` | Benchmark | SCAFFOLDED |
| Isolation Forest | L4 | scikit-learn | `l4_divergence.isolation_forest`| Benchmark | SCAFFOLDED |
| Emergent Capability Envelope | L4 | Statistical bounds | `l4_divergence.ece` | Adversarial | SCAFFOLDED |
| RiskChain temporal graph | L5 | NetworkX | `l5_riskchain.graph` | Integration | SCAFFOLDED |
| Bayesian conditional risk | L5 | Belief network | `l5_riskchain.bayesian` | Integration | SCAFFOLDED |
| Neuro-Fuzzy governance | L5 | scikit-fuzzy FIS | `l5_riskchain.governance` | Integration | SCAFFOLDED |
| cgroup-scoped SIGSTOP | L3/L5 | Kernel enforcement | `l3_ebpf.enforcement` | Security | SCAFFOLDED |
| BLAKE3 ECES hash chain | L5 | Cryptographic chain | `l5_riskchain.eces` | Unit | SCAFFOLDED |
| Hardware-backed signing | H4 | TPM 2.0 | `security.keys` | Security | SCAFFOLDED |
| TEE-based engine isolation | H1 | TDX / SEV-SNP | `security.tee` | Integration | SCAFFOLDED |
| TOCTOU-resistant file identity | H2 | Inode/Device binding| `l2_sdn.toctou` | Security | SCAFFOLDED |
| perf_event_open telemetry | H3 | CPU counters | `common.hpc.provider` | Benchmark | SCAFFOLDED |
| Forensic evidence generation | H4 | X.509 + ECES | `l5_riskchain.forensic` | Security | SCAFFOLDED |

> Note: No features are marked as VALIDATED or IMPLEMENTED yet, as this is Phase 1 (Scaffolding and Contracts).
