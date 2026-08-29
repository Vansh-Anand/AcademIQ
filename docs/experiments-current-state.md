# Existing Experiment Infrastructure

## 1. Existing benchmark components
The `benchmarks/` directory currently houses isolated performance benchmarks:
- **L1 GCD**: `benchmarks/gcd_real_model/benchmark_gcd.py` (Tokens/sec and generation overhead).
- **L2 SDN**: `benchmarks/latency/sdn_benchmark.py` (Normalization latency).
- **L3 Native**: `benchmarks/linux_native/l3_validation_runner.py` (Linux kernel hook validation).

## 2. Existing test fixtures
- `tests/fixtures/telemetry/execve_trace.jsonl` contains pre-recorded benign and malicious system call traces for testing L3/L4 offline.
- `tests/integration/` contains dozens of hardcoded adversarial logic test cases (e.g., 20 distinct obfuscation payloads for L2, multi-step exfiltration flows for L5).

## 3. Event injection capabilities
- **Agent/L1 Action**: Fully injectable via `AcademiqOrchestrator.process_event(ToolInvocationEvent(...))`
- **L2 Shell**: Fully injectable directly via `L2Interceptor.intercept(ShellCommandEvent(...))`
- **L3 Telemetry**: Fully injectable via `SimulatedL3Collector.run_replay()` loading arbitrary JSON traces.

## 4. L1 integration capability
- The repository already contains a real-model HuggingFace wrapper (`GCDLogitsProcessor`) that successfully restricts token generation via the PDA compiled from `config/policies/gcd.yaml`.

## 5. L2 integration capability
- The `DevelopmentShellInterceptor` natively canonicalizes complex shell commands, stripping base64/ANSI-C/path traversal obfuscation before checking against allowed policies.

## 6. L3 simulation capability
- `SimulatedL3Collector` allows completely native-free Windows execution by processing `.jsonl` trace files and triggering the standard L3/L4 callbacks.

## 7. L4 invocation capability
- The `IsolationForestDetector` can ingest numerical feature arrays (representing syscall paths) directly and output divergence scores without requiring real live kernel telemetry.

## 8. L5 invocation capability
- `BayesianRiskModel` dynamically calculates multi-step attack probabilities.
- `FuzzyGovernanceEngine` dictates ALLOW, WARN, THROTTLE, or FREEZE states programmatically based on the rolling Bayesian evidence.

## 9. ECES evidence capability
- `EvidenceChainWriter` automatically logs security events into an append-only store with cryptographic hash chaining (BLAKE3/SHA256).

## 10. Existing metrics
- Output from test suites and benchmarks already measures sub-millisecond execution times in L1/L2, and isolation accuracy in L4. The pipeline naturally timestamps events (using `time.time_ns()`), making latency tracking trivial.

## 11. Existing CLI support
- The CLI (`cli/main.py`) supports simulated pipeline runs (`run --mode simulation`), manual SDN normalization analysis (`sdn analyze`), and hardware status checks.

## 12. Reusable components
- The `AcademiqOrchestrator` itself acts as a unified entrypoint.
- The scenarios in `test_l5_riskchain.py` act as a miniature sequencing framework that can be lifted and expanded for the 5 formal experiments.

## 13. Missing components
- **Unified Scenario Harness**: Currently, L1/L2 testing and L3/L4 telemetry replay are completely isolated in their respective unit/integration test files. We lack a unified `ExperimentRunner` that simultaneously feeds a malicious `ToolInvocationEvent` *and* an accompanying `L3 Trace` to represent a single, cohesive attacker payload moving through all defenses.

## 14. Minimum changes required for EXP-1
- Create a reusable experiment runner script.
- Define EXP-1 (Direct Prompt Injection) as an object combining a forbidden `ToolInvocationEvent` (e.g. `sys_exec`) with a mocked L3 telemetry file (should it hypothetically bypass L1/L2).
- Route it through the existing orchestrator and verify that the pipeline correctly terminates the attack at L1/L2 (emitting `DecisionEnum.BLOCK`).

## 15. Recommended next implementation step
Create `benchmarks/experiments/runner.py` and implement a base `ExperimentHarness` class capable of taking a `ScenarioDefinition` (consisting of Agent Events and simulated L3 Traces) and executing it end-to-end through the existing `AcademiqOrchestrator`.


