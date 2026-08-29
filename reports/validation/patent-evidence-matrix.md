# Patent Evidence Matrix

| Feature | Technical Implementation | Concrete File | Validation Status |
|---------|-------------------------|---------------|-------------------|
| Grammar-Constrained Decoding | Softmax Logit Masking (-inf) | `l1_gcd/masking.py` | UNIT TESTED |
| Semantic Deobfuscation | Bashlex AST Normalization | `l2_sdn/normalizers.py` | INTEGRATION TESTED |
| TOCTOU Execution Gate | Inode caching / file handles | `l2_sdn/toctou/resolver.py` | INTEGRATION TESTED |
| Kernel Agent Telemetry | eBPF sys_enter hooks | `l3_ebpf/collector.py` | SIMULATION VALIDATED |
| Divergence Embedding | Siamese Recurrent Autoencoder | `l4_divergence/models/siamese.py` | INTEGRATION TESTED |
| Neuro-Fuzzy Governance | Fuzzy logic thresholds (ALLOW/WARN) | `l5_riskchain/governance/fuzzy.py` | INTEGRATION TESTED |
| ECES Tamper Evidence | Cryptographic Causal Chain | `l6_eces/chain/writer.py` | INTEGRATION TESTED |
| TEE Nonce Attestation | TDX/SEV-SNP Quote generation | `l7_trust/attestation/verifier.py` | SIMULATION VALIDATED |
