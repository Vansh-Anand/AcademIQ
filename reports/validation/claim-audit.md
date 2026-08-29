# Claim-to-Code Audit

## Claim 1: "Pre-softmax logit masking"
- **Implementation File**: `l1_gcd/masking.py`
- **Function/Class**: `LogitMasker`
- **Test**: `tests/unit/test_gcd.py`
- **Validation Type**: Synthetic logits
- **Status**: UNIT TESTED
- **Limitation**: Depends on accurate tokenization.

## Claim 2: "Command canonicalization"
- **Implementation File**: `l2_sdn/canonicalizer.py`
- **Function/Class**: `CommandCanonicalizer`
- **Test**: `tests/unit/test_l2.py`, `tests/integration/test_l2_adversarial.py`
- **Validation Type**: 20 Adversarial Cases
- **Status**: INTEGRATION TESTED
- **Limitation**: Obfuscations via newly undiscovered binaries are not generically decoded.

## Claim 3: "eBPF Host-Only Agent Monitoring"
- **Implementation File**: `l3_ebpf/collector.py`
- **Function/Class**: `NativeEBpfCollector`, `SimulationEBpfCollector`
- **Test**: `tests/integration/test_l3_ebpf.py`
- **Validation Type**: Simulation Test
- **Status**: SIMULATION VALIDATED
- **Limitation**: NOT AVAILABLE ON CURRENT HOST (Windows).

## Claim 4: "Siamese Telemetry Embedding"
- **Implementation File**: `l4_divergence/models/siamese.py`
- **Function/Class**: `SiameseRecurrentAutoencoder`
- **Test**: `tests/integration/test_l4_divergence.py`
- **Validation Type**: Synthetic Data Pipeline
- **Status**: INTEGRATION TESTED
- **Limitation**: Not tuned on empirical attack sets.

## Claim 5: "Neuro-Fuzzy Governance"
- **Implementation File**: `l5_riskchain/governance/fuzzy.py`
- **Function/Class**: `FuzzyGovernanceEngine`
- **Test**: `tests/integration/test_l5_riskchain.py`
- **Validation Type**: Scenario execution (Safe, Exfil, Process Manip)
- **Status**: INTEGRATION TESTED
- **Limitation**: Heuristically configured membership functions.

## Claim 6: "Cryptographic Causal ECES Log"
- **Implementation File**: `l6_eces/chain/writer.py`
- **Function/Class**: `EvidenceChainWriter`
- **Test**: `tests/integration/test_l6_eces.py`
- **Validation Type**: Tamper Tests
- **Status**: INTEGRATION TESTED
- **Limitation**: Relies on host timestamp integrity if TEE is missing.

## Claim 7: "Hardware-Anchored Security Domain"
- **Implementation File**: `l7_trust/domain/isolation.py`, `l7_trust/detector.py`
- **Function/Class**: `IsolationVerifier`, `ConfidentialComputingDetector`
- **Test**: `tests/integration/test_l7_trust.py`
- **Validation Type**: Simulation Replay & Configuration verification
- **Status**: SIMULATION VALIDATED
- **Limitation**: TDX / SEV-SNP native hardware not tested.
