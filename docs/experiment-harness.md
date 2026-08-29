# AcademIQ Experiment Harness

## 1. Why the harness exists
As AcademIQ moves into Phase 3 (Real Adversarial Agent Experiments), we need a unified orchestration layer to test scenarios (EXP-1 through EXP-5) end-to-end. Previously, each security layer (L1 GCD, L2 SDN, L3/L4 Telemetry) was tested in isolation using layer-specific mock events. 

The `ExperimentHarness` exists to string these layers together natively, feeding a single `ScenarioDefinition` into the existing `AcademiqOrchestrator` and tracking the end-to-end traversal, latency, and exact security outcomes (Allow/Block) at each boundary.

## 2. How it reuses the existing pipeline
The harness does **not** duplicate any security logic. It directly imports the production `AcademiqOrchestrator` from `orchestrator/pipeline/core.py`. When a scenario defines an `agent_event`, the harness simply passes it to `orchestrator.process_event()`. The orchestrator inherently executes L1 constraints, hands off to the L2 `DevelopmentShellInterceptor`, simulates L3/L4 events via native schemas, correlates them in L5 RiskChain, and writes to L6 ECES.

## 3. ScenarioDefinition structure
A `ScenarioDefinition` strictly defines a reproducible experimental case:
- `scenario_id` (str): Unique identifier (e.g. `EXP-1`)
- `scenario_name` (str): Human-readable name
- `description` (str): Intent of the experiment
- `category` (str): Classification (e.g. `PROMPT_INJECTION`)
- `agent_events` (List[ToolInvocationEvent]): The initial LLM tool calls.
- `shell_events` (List[ShellCommandEvent]): Direct shell events if skipping L1.
- `telemetry_trace` (Optional[str]): A `.jsonl` file to replay in L3.
- `expected_security_outcome` (DecisionEnum): What the pipeline *should* do (ALLOW/BLOCK).

## 4. ExperimentResult structure
The `ExperimentResult` captures exactly what occurred during the scenario run:
- `total_latency_ns`: Computed via high-resolution `time.perf_counter_ns()`.
- `layer_outcomes`: A mapping of L1 through L5, denoting whether the layer was `NOT_EXECUTED`, `ALLOW`, or `BLOCK`.
- `attack_blocked`: Boolean indicating if the pipeline terminated execution.
- `attack_success`: Boolean indicating if a malicious payload successfully bypassed all layers.
- `stopping_layer`: Identifies the exact layer that blocked the attack (e.g. `L2`).
- `evidence_reference`: The session ID representing the ECES cryptographic trace.

## 5. Event flow
1. Harness creates the `AcademiqOrchestrator`.
2. Harness records `start_ns`.
3. Harness iterates `agent_events`, passing them to `process_event()`.
4. Orchestrator traverses L1 -> L2 -> L3/L4 -> L5.
5. If any layer returns `DecisionEnum.BLOCK`, execution halts immediately.
6. Harness extracts the `source_layers` visited and the final decision, populating the `LayerOutcomes`.
7. Harness records `end_ns` and returns the `ExperimentResult`.

## 6. Plugging in EXP-1 through EXP-5
Future experiments will simply define new `ScenarioDefinition` fixtures:
- **EXP-1**: Define `agent_events` with forbidden tools. Expect `L1` to block.
- **EXP-2**: Define `agent_events` with obfuscated shell payloads. Expect `L2` to block.
- **EXP-3/4**: Supply complex multi-event lists and a `telemetry_trace` mapping. Expect `L4/L5` to block via RiskChain.

## 7. Telemetry Replay Integration (Dependency Injection)

To evaluate telemetry traces independently without launching a native kernel ringbuffer, the orchestrator and harness support **Dependency Injection** of the `SimulatedL3Collector`.

### Default Behavior
By default, the `AcademiqOrchestrator` runs completely isolated. If `l3_collector` is `None`, L3, L4, and L5 outcomes are mocked deterministically based on static data (this allows unit tests and UI evaluation to function without tracing).

### Injected Collector Behavior
If `ScenarioDefinition.telemetry_trace` is provided, the `ExperimentHarness` will:
1. Initialize an `AgentScopeManager` matching the fixture's scoping (`test_agent_1`, `cgroup=1000`).
2. Initialize a `SimulatedL3Collector` pointing to the `.jsonl` trace file.
3. Inject the collector into the `AcademiqOrchestrator`, which overrides the default mocks.
4. Call `run_replay()` on the collector to fire the events through the pipeline asynchronously.

### Correlation Limitations
Currently, L4 Divergence and L5 RiskChain expect native integration layers that aren't natively implemented in `process_event()`. Thus, when traces are replayed:
- L3 outcomes are accurately marked `ALLOW` or `BLOCK` (based on `ExecutionCorrelationManager` detecting anomalies).
- L4 and L5 are currently marked as `UNAVAILABLE` inside the `ExperimentResult` until they are formally wired into the native callback stream.

### Future Use (EXP-3, EXP-4, EXP-5)
Future adversarial experiments (EXP-3 Multi-Step Exfiltration, EXP-4 Privilege Escalation, EXP-5 Novel Attacks) will heavily rely on providing `telemetry_trace` files holding actual Linux eBPF captured traces from the attack scenarios. The harness will automatically stream them, allowing L3/L4/L5 rule logic to be iteratively tuned.

## 8. Optional Layers
If a scenario tests native shell capabilities directly (bypassing L1 Agent completely), it populates `shell_events` instead of `agent_events`. The harness recognizes this and forwards directly to the L2 `DevelopmentShellInterceptor`, marking L1 as `NOT_EXECUTED`.

## 9. Latency Measurement
End-to-end latency is measured using Python's `time.perf_counter_ns()` wrapper around the `process_event` boundary. Because the existing orchestrator is tightly coupled, adding per-layer timing would require invasive modification to production security logic which violates testing constraints. Only holistic timing is guaranteed unless individual layers expose internal metrics.

## 10. What this harness does NOT simulate or replace
This harness is purely an integration testing tool. It does NOT:
- Implement any ML isolation logic.
- Connect to native eBPF hooks (it uses `SimulatedL3Collector` data).
- Invoke real external LLM APIs natively (it uses the static agent events provided in the scenario definition).
