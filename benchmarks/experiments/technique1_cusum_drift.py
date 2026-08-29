import os
import sys
import json
import time
import numpy as np
import random

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from l4_divergence.ece.manager import ECEManager
from l4_divergence.ece.policy import BaselineAdmissionPolicy
from common.events.schemas import WindowQuality

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "technique1_cusum_drift")
os.makedirs(RESULTS_DIR, exist_ok=True)

def generate_scores(n, mean, std):
    return [max(0.0, min(1.0, random.gauss(mean, std))) for _ in range(n)]

def run_experiment():
    random.seed(42)
    np.random.seed(42)
    
    # Setup ECE Manager and Policy
    initial_scores = generate_scores(1000, 0.4, 0.05)
    manager = ECEManager(percentile=99.0)
    manager.initialize(initial_scores)
    manager.enable_drift_detection(reference_value=0.05, decision_threshold=1.5, min_admitted_samples=50)
    
    initial_threshold = manager.threshold
    print(f"Initial Baseline Mean: {manager.get_baseline_mean():.4f}")
    print(f"Initial ECE Threshold (99th pct): {initial_threshold:.4f}")
    
    quality_good = WindowQuality(
        event_count=100, expected_count=100, dropped_events=0,
        ordering_valid=True, timestamp_quality=1.0, hpc_coverage=1.0, quality_score=1.0
    )
    
    metrics = {
        "stable_drift_detected": False,
        "attack_outlier_triggered_recalibration": False,
        "sustained_drift_detected": False,
        "recalibration_successful": False,
        "observations_until_detection": 0,
        "old_threshold": initial_threshold,
        "new_threshold": 0.0,
        "threshold_delta": 0.0,
        "rejected_poisoning_candidates": 0,
        "admitted_recalibration_samples": 0,
        "mean_latency_ms": 0.0
    }
    
    latency_records = []
    
    # -----------------------------------------------------------------
    # SCENARIO A: STABLE BEHAVIOR
    # -----------------------------------------------------------------
    print("\n--- SCENARIO A: STABLE BEHAVIOR ---")
    stable_scores = generate_scores(200, 0.4, 0.05)
    
    for score in stable_scores:
        policy = BaselineAdmissionPolicy(current_threshold=manager.threshold, margin=0.2)
        is_admitted = policy.is_admissible(score, quality_good)
        
        start = time.perf_counter_ns()
        manager.process_observation(score, is_admitted)
        latency_records.append(time.perf_counter_ns() - start)
        
    print(f"State after stable: {manager.drift_detector.state.value}")
    if manager.drift_detector.state.value != "STABLE":
        metrics["stable_drift_detected"] = True

    # -----------------------------------------------------------------
    # SCENARIO B: SINGLE ATTACK OUTLIER
    # -----------------------------------------------------------------
    print("\n--- SCENARIO B: SINGLE ATTACK OUTLIER ---")
    attack_scores = [0.95, 0.98, 0.99] # Anomalous high scores
    
    for score in attack_scores:
        policy = BaselineAdmissionPolicy(current_threshold=manager.threshold, margin=0.2)
        is_admitted = policy.is_admissible(score, quality_good)
        
        start = time.perf_counter_ns()
        manager.process_observation(score, is_admitted)
        latency_records.append(time.perf_counter_ns() - start)
        
    print(f"State after attack outliers: {manager.drift_detector.state.value}")
    print(f"Rejected Candidates: {manager.drift_detector.rejected_candidates}")
    
    if manager.drift_detector.state.value != "STABLE":
        metrics["attack_outlier_triggered_recalibration"] = True
    
    # -----------------------------------------------------------------
    # SCENARIO C: SUSTAINED LEGITIMATE DISTRIBUTION SHIFT
    # -----------------------------------------------------------------
    print("\n--- SCENARIO C: SUSTAINED LEGITIMATE DISTRIBUTION SHIFT ---")
    # Shift mean from 0.4 to 0.55. (Below current_threshold + margin so it gets admitted)
    shift_scores = generate_scores(300, 0.55, 0.05)
    
    for score in shift_scores:
        policy = BaselineAdmissionPolicy(current_threshold=manager.threshold, margin=0.2)
        is_admitted = policy.is_admissible(score, quality_good)
        
        start = time.perf_counter_ns()
        recalibrated = manager.process_observation(score, is_admitted)
        latency_records.append(time.perf_counter_ns() - start)
        
        if recalibrated:
            metrics["recalibration_successful"] = True
            metrics["new_threshold"] = manager.threshold
            metrics["threshold_delta"] = manager.threshold - initial_threshold
            break
            
    print(f"State after shift: {manager.drift_detector.state.value}")
    if manager.drift_detector.drift_detections > 0:
        metrics["sustained_drift_detected"] = True
        
    metrics["observations_until_detection"] = manager.drift_detector.observations_until_detection
    metrics["rejected_poisoning_candidates"] = manager.drift_detector.rejected_candidates
    metrics["admitted_recalibration_samples"] = manager.drift_detector.admitted_samples
    metrics["mean_latency_ms"] = float(np.mean(latency_records) / 1_000_000)
    
    print("\n--- RESULTS ---")
    for k, v in metrics.items():
        print(f"{k}: {v}")
        
    summary = {
        "technique": "CUSUM Adaptive ECE Recalibration",
        **metrics
    }
    
    with open(os.path.join(RESULTS_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=4)
        
    raw = {
        "stable_scores": stable_scores,
        "attack_scores": attack_scores,
        "shift_scores": shift_scores
    }
    with open(os.path.join(RESULTS_DIR, "raw_results.json"), "w") as f:
        json.dump(raw, f, indent=4)
        
    print(f"\nExperiment Results saved to {RESULTS_DIR}")

if __name__ == "__main__":
    run_experiment()
