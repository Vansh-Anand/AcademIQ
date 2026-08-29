# Technique 1: Adaptive ECE Recalibration Using CUSUM Drift Detection

## 1. Problem with Static Behavioral Baselines
In AcademIQ's Layer 4 (Behavioral Divergence) engine, the Emergent Capability Envelope (ECE) threshold is calculated initially based on a baseline of legitimate behavior. However, static baselines suffer from concept drift. Over time, an agent's legitimate task distribution, computational workload, or interaction frequency can change structurally. If the threshold is completely static, this drift causes an escalating false-positive rate. Conversely, automatically recalculating the threshold purely on recent data makes the system vulnerable to **baseline poisoning**, where an attacker slowly injects anomalies until the engine accepts them as "normal".

## 2. Solution: Security-Gated Adaptive Recalibration
This enhancement introduces a strictly controlled, adaptive behavioral baseline recalibration sequence driven by mathematical sustained drift evidence. It uses Cumulative Sum (CUSUM) control charts to identify true distributional drift, securely sequestered behind admission policies to prevent automated poisoning.

## 3. Existing ECE Architecture
- `ECEManager`: Handles storing the ECE baseline scores and the calculated anomaly threshold.
- `BaselineAdmissionPolicy`: An existing component acting as a strict firewall that drops any significantly anomalous or invalid execution windows, preventing them from modifying standard histories.

## 4. CUSUM Mathematical Formulation
The `CUSUMDriftDetector` computes cumulative deviations from the expected baseline mean ($\mu_0$). For each admitted behavioral divergence score ($x_t$):

- **Positive Drift (S+)**: $\max(0, S^+_{t-1} + (x_t - \mu_0 - k))$
- **Negative Drift (S-)**: $\max(0, S^-_{t-1} + (\mu_0 - x_t - k))$

Where:
- $k$: Reference value representing allowable distribution slack (noise tolerance).
- $h$: Decision threshold. If $S^+$ or $S^-$ exceeds $h$, mathematical drift is formally suspected.

## 5. Drift State Machine
The detector explicitly transitions through rigorous states:
1. `STABLE`: System is normal.
2. `OBSERVING`: Minor cumulative deviations accumulating.
3. `DRIFT_SUSPECTED`: The threshold $h$ is exceeded.
4. `RECALIBRATION_PENDING`: Collecting a designated buffer of new, trusted observations.
5. `RECALIBRATED`: Buffer met, threshold updated, resetting back to `STABLE`.

## 6. Security-Gated Observation Admission & Anti-Poisoning
**Crucial Security Property**: The CUSUM state machine does *not* blindly process every event. 
1. The raw event must first be evaluated by the existing L4 anomaly detector.
2. The score is submitted to the `BaselineAdmissionPolicy`.
3. If the score is excessively high (representing an attack outlier) or the window quality is poor, the observation is *rejected* and dropped.
4. Only formally admitted observations update the CUSUM state or enter the recalibration candidate buffer.

Because of this, an attacker attempting to spike the divergence score to force recalibration will hit the admission firewall, resulting in their data being dropped before the drift detector even evaluates it.

## 7. Recalibration Workflow
When $h$ is breached (entering `DRIFT_SUSPECTED`), the system does not immediately rewrite the ECE threshold.
1. It transitions to `RECALIBRATION_PENDING` and begins populating a `candidate_buffer`.
2. It waits until exactly `minimum_admitted_samples` (e.g., 50) have been gathered (all passing the admission policy).
3. Once collected, these new verified baseline samples are injected into the standard `ECEManager` history array.
4. The exact `percentile` recalculation is executed.
5. The state machine resets to `STABLE`.

## 8. Configuration Parameters
Governed by `config/policies/divergence.yaml`:
```yaml
drift_detection:
  enabled: true
  monitored_signal: divergence_score
  cusum:
    reference_value: 0.05
    decision_threshold: 1.5
  recalibration:
    minimum_admitted_samples: 50
    percentile: 99
```

## 9. Experimental Scenarios (technique1_cusum_drift.py)
Three controlled scenarios validate the mechanics natively:
- **SCENARIO A (Stable):** 200 normal events. `STABLE` remains.
- **SCENARIO B (Attack Outlier):** 3 heavily anomalous attacks are injected. **Result:** Rejected by admission gates, no poisoning occurs, state remains `STABLE`.
- **SCENARIO C (Sustained Drift):** 300 legitimate events simulating a new mean (shifted by +0.15). **Result:** CUSUM detects the sustained positive accumulation, triggers drift, safely buffers 50 samples, and recalibrates the threshold higher to accommodate the new normal.

## 10. Limitations
- **Fail Closed Mechanism:** If an agent drifts so rapidly and violently that it trips the `BaselineAdmissionPolicy` margin before the CUSUM can trigger, the system interprets it as a massive anomaly and blocks recalibration. This requires human manual review to reset the sandbox (which is the intended secure failure mode).
- The reference value $k$ and threshold $h$ require careful tuning based on expected agent interaction frequencies in production.
