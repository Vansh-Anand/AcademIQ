# AcademIQ Phase 5: L4 Behavioral Divergence Engine

The L4 Behavioral Divergence Engine is responsible for continuously evaluating the stream of system calls (and hardware performance counters) executed by the agent, determining whether the agent's behavior has diverged from its expected *legitimate capability envelope*.

## Patent Feature Mapping
1. **Pure syscall topology**: IMPLEMENTED. Extracting canonical syscall strings without raw paths.
2. **Sliding 256-event window**: IMPLEMENTED (`TrajectoryWindow`).
3. **Stride 64**: IMPLEMENTED (`TrajectoryWindow`).
4. **Siamese recurrent encoder**: IMPLEMENTED (`SiameseRecurrentAutoencoder`).
5. **LSTM**: IMPLEMENTED.
6. **Latent representation**: IMPLEMENTED.
7. **Isolation Forest**: IMPLEMENTED (`IsolationForestDetector`).
8. **Soft-voting ensemble**: IMPLEMENTED (`DivergenceEnsemble`).
9. **Emergent Capability Envelope (ECE)**: IMPLEMENTED (`ECEManager`).
10. **Dynamic percentile threshold**: IMPLEMENTED.
11. **Periodic recalibration**: IMPLEMENTED.
12. **Telemetry-health awareness**: IMPLEMENTED (`WindowQuality` schema).
13. **Hardware performance counter fusion**: IMPLEMENTED (`HardwareTelemetryProvider`).
14. **Cache-miss telemetry**: IMPLEMENTED.
15. **Instructions/cycles (IPC)**: IMPLEMENTED.
16. **Behavioral mimicry augmentation**: IMPLEMENTED (via SimulatedHPCProvider anomalies).

## Datasets and Telemetry
L4 operates entirely on structural behavior. It does not train on prompt text or shell command strings.
When executing natively on Windows, it uses `SimulatedHPCProvider` to mock hardware cache/instruction variations that might be seen in an actual Linux environment.
Linux execution supports `LinuxPerfEventProvider` wrapping `perf_event_open`.

## Emergent Capability Envelope (ECE)
The system maintains a dynamic threshold derived from the 99th percentile of legitimate divergence scores.
To prevent poisoning attacks, the `BaselineAdmissionPolicy` rejects windows with poor telemetry quality or explicitly anomalous scores from entering the envelope.

## Phase 6 Handoff
Phase 5 finishes by producing a standardized `DivergenceResult`. Phase 6 (L5 RiskChain) will consume these results, blend them with L2/L3 context, and perform fuzzy-logic governance to issue WARN, THROTTLE, or FREEZE decisions against the container cgroups.
