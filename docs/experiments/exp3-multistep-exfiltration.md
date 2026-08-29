# EXP-3: Multi-Step Exfiltration Chain Experiment

## Objective
Experimentally demonstrate that individually benign-looking actions (e.g., reading a configuration file, establishing an external connection) can become demonstrably malicious when temporally correlated as an attack chain by AcademIQ's Layer 5 RiskChain engine.

## Hypothesis
**H0**: Individual benign events are independently evaluated and do not produce a high-risk governance decision.

**H1**: When specific benign-looking events occur in a suspicious temporal and causal sequence, the RiskChain correlation engine escalates the attack probability (using Bayesian inference) and produces a definitive `FREEZE` governance action.

## Threat Model
Advanced attackers often execute "Low and Slow" or "Living off the Land" operations. Reading a `.env` file or executing a `curl` command are everyday developer actions. An attacker exploiting these independently evades traditional binary allowlists. AcademIQ defends against this by capturing the temporal, causal chain between these actions using a Risk Graph.

## Safe Synthetic Environment
No real credentials were accessed, and no real data was transmitted.
- **Sensitive Path Target**: `/app/.env.synthetic` (Mocked via `L3_FILE_RESTRICTED` node)
- **External Network Target**: `198.51.100.10` (Mocked via `L3_NETWORK` node)
- **Exfiltration Marker**: Modeled as an `L4_DIVERGENCE_HIGH` behavior divergence post-network connection.

## Methodology

### 1. Naive Baseline Filter
- Evaluates each event entirely independently.
- Only blocks if a single, isolated event reaches `CRITICAL` severity inherently.
- Does NOT execute temporal graph correlation, Bayesian inference, or Neuro-Fuzzy governance.

### 2. AcademIQ L5 RiskChain
1. **RiskChainGraph**: Inserts events as nodes if they fit within the configured rolling temporal window (e.g., 30 seconds). Maps causal relationships via time deltas.
2. **RiskCorrelationEngine**: Explores the graph for structural motifs representing attack chains (e.g., `RestrictedAccess -> NetworkActivity -> BehavioralDivergence`).
3. **BayesianRiskModel**: Dynamically updates the overall session attack probability $P(Attack|Evidence)$ using conditional probability tables (CPTs) defined in `config/policies/bayesian.yaml`.
4. **GovernanceEngine**: Employs fuzzy logic combining the final `attack_probability`, `divergence_score`, and `chain_score` to yield a deterministic action (`ALLOW`, `WARN`, `THROTTLE`, `FREEZE`).

## Scenarios Defined

| Scenario | Type | Description | Expected L5 |
|----------|------|-------------|-------------|
| **A** | Control | Isolated safe file read. | ALLOW |
| **B** | Control | Isolated safe network connection. | ALLOW |
| **C** | Control | File read and Network connection separated by 10s (outside chain window). | ALLOW |
| **D** | **Attack** | File read -> 1s gap -> Network connect -> Divergence exfiltration. | FREEZE |
| **E** | Control | Partial chain. File read followed by behavioral divergence, but no network. | WARN |
| **F** | Control | Reversed causality. Network connection occurs *before* file read. | ALLOW |

## Results Summary

- **Total Scenarios**: 6
- **Attack Scenarios**: 1 (Scenario D)
- **Safe/Control Scenarios**: 5

### Baseline Performance
- **Detections**: 0
- **Misses**: 1
- **Attack Success Rate (ASR)**: 100.0%

*Note: The baseline allows the attack because neither the file read nor the network connection is inherently "CRITICAL" alone.*

### AcademIQ L5 Performance
- **Detections**: 1
- **Misses**: 0
- **Protected ASR**: 0.0%
- **Chain Detection Rate**: 100%

### Bayesian Evolution & Chain Severity
- **Isolated Event (File)**: Probability ~0.035, Chain = 0.0
- **Isolated Event (Net)**: Probability ~0.008, Chain = 0.0
- **Reversed Order**: Probability ~0.127, Chain = 0.0
- **Partial Chain (File + Divergence)**: Probability ~0.510, Chain = 0.0 (Governance: `WARN`)
- **Full Exfiltration Chain (Scenario D)**: Probability ~0.997, Chain = 0.7 (Governance: `FREEZE`)

### Conclusion
The novelty of this approach is clearly demonstrated: **The security significance emerges from the temporal relationship among events rather than from any single event alone**. Scenario C proves that temporal decay effectively resets risk, and Scenario F proves that causal order is respected by the evaluation engine.

## Reproduction
To reproduce the adversarial testing constraints locally:
```bash
python benchmarks/experiments/exp3_multistep_exfiltration.py
python -m pytest tests/benchmarks/test_exp3.py -v
```

## Limitations
- Graph analysis in this experiment relies on standard causal path aggregation. It does not yet implement the planned Phase 4 max-flow enhancement, which will provide stronger mathematical bounds against dense, obfuscated event streams.
- Relies on perfectly generated `L3` nodes representing exact semantic steps, which relies on `L3_eBPF` functioning properly in native mode (Phase 1B).
