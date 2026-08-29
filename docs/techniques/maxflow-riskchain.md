# Technique 2: RiskChain Max-Flow Attack Path Analysis

## Objective
The goal of Technique 2 is to enhance the AcademIQ L5 RiskChain by systematically identifying the "Highest-Risk Causal Attack Chain". Instead of relying solely on pattern-matching or topological shortest-paths, this technique treats the temporal event structure as a **Directed Acyclic Graph (DAG)** and executes a longest-path maximization based on event risk contribution.

## Architecture

### `RiskPathAnalyzer` (`l5_riskchain/graph/analyzer.py`)
This component evaluates the existing `RiskChainGraph` and extracts the sequence of nodes that yields the highest cumulative risk score.

**Key Design Decisions:**
1. **Not Ford-Fulkerson**: Standard Max-Flow computes volumetric throughput capacities. In causal security events, risk does not "split" across paths like water in pipes.
2. **DAG Optimization**: Since the graph represents a timeline (enforced via timestamps), cycles cannot causally exist. A topological sort combined with a dynamic programming longest path algorithm efficiently calculates the exact chain that maximizes total severity.
3. **Deterministic Fingerprinting**: The analyzer generates a signature string (e.g. `L3_FILE_RESTRICTED->L3_NETWORK->L4_DIVERGENCE_HIGH`) and hashes it using the global `HashProvider` (`BLAKE3` or `SHA-256`) to construct an immutable event chain fingerprint.

## Benchmarks (`technique2_maxflow_riskchain.py`)
Five benchmark scenarios formally validate this mechanism:

| Scenario | Name | Description | Output |
|----------|------|-------------|--------|
| A | Full Exfiltration | High-risk linear chain. | Extracts path, validates fingerprint. |
| B | Competing Paths | Graph contains noisy low-risk branches and one high-risk branch. | Correctly ignores low-risk path, extracts highest risk chain. |
| C | Reversed Causal Order | A path exists but timestamps flow backwards. | Causal verification fails, prevents false positives. |
| D | Partial Chain | A partial, incomplete chain. | Extracts lower risk signature correctly. |
| E | Structurally Equivalent | Same semantic types as A, but different local node IDs. | Hash fingerprint explicitly matches Scenario A. |

## Impact on L5 Pipeline
The `RiskPathAnalyzer` integrates directly into the `ExperimentHarness` pipeline. When a valid high-risk path is structurally verified, it explicitly elevates the `chain_score` severity evaluated by the fuzzy `GovernanceEngine`, increasing the probability of a decisive `FREEZE` or `BLOCK` decision.
