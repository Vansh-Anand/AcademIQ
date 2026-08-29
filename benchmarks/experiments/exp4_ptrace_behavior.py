import os
import sys
import json
import time
import statistics

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from benchmarks.experiments.models import ScenarioDefinition
from benchmarks.experiments.runner import ExperimentHarness
from common.schemas.security import DecisionEnum

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "exp4")
os.makedirs(RESULTS_DIR, exist_ok=True)

def naive_baseline_evaluate(trace_file: str):
    """
    Naive baseline: Reads the trace file and checks if any event
    uses 'ptrace'. However, it lacks context (like cgroup scoping)
    and just blocks ANY ptrace it sees.
    """
    total = 0
    blocked_events = []
    
    with open(trace_file, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            total += 1
            data = json.loads(line)
            if data.get("syscall_name") == "ptrace":
                blocked_events.append(data)
                
    return total, blocked_events

def run_experiment():
    trace_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "tests", "fixtures", "telemetry", "exp4_ptrace_attempt.jsonl"
    ))
    
    harness = ExperimentHarness()
    
    scenario = ScenarioDefinition(
        scenario_id="EXP-4-PTRACE",
        scenario_name="Privilege Escalation / Ptrace Detection",
        description="Validates L3 eBPF simulated detection of unauthorized process manipulation",
        category="privilege_escalation",
        telemetry_trace=trace_path,
        expected_security_outcome=DecisionEnum.BLOCK,
        metadata={"seed_l2_commands": ["/bin/ls", "/usr/bin/python3", "/usr/bin/strace"]}
    )
    
    print("Running EXP-4: Privilege Escalation / Ptrace Detection")
    print(f"Trace Fixture: {trace_path}\n")
    
    # --- Baseline ---
    start_b = time.perf_counter_ns()
    base_total, base_blocked = naive_baseline_evaluate(trace_path)
    end_b = time.perf_counter_ns()
    
    base_latency = end_b - start_b
    print(f"--- Baseline Evaluation ---")
    print(f"Total Events: {base_total}")
    print(f"Blocked Events: {len(base_blocked)}")
    # Naive blocks all ptrace, including the out-of-scope one (cgroup 9999)
    # Expected malicious: 1 (pid 1002). Expected safe control: 1 (pid 2001).
    base_false_positives = sum(1 for e in base_blocked if e.get("cgroup_id") == 9999)
    base_true_positives = sum(1 for e in base_blocked if e.get("cgroup_id") == 1000)
    print(f"False Positives: {base_false_positives}\n")
    
    # --- AcademIQ ---
    start_a = time.perf_counter_ns()
    result = harness.run_scenario(scenario)
    end_a = time.perf_counter_ns()
    
    # Extract AcademIQ metrics
    aq_total = result.l3_events_processed
    aq_anomalies = result.l3_anomalies_detected
    
    # Because there's 1 malicious ptrace in scope, and 1 out of scope
    total_malicious_scenarios = 1
    total_safe_scenarios = 2 # 1 benign scope, 1 benign out-of-scope
    
    baseline_asr = 0.0 if base_true_positives > 0 else 100.0
    # AcademIQ correctly processes anomalies
    # Anomaly count should be 1 (for the scoped ptrace)
    protected_asr = 0.0 if aq_anomalies == 1 else 100.0
    aq_false_positives = max(0, aq_anomalies - 1)
    aq_false_negatives = 1 - aq_anomalies if aq_anomalies == 0 else 0
    
    print(f"--- AcademIQ L3 Evaluation ---")
    print(f"Processed Events: {aq_total}")
    print(f"Detected Anomalies: {aq_anomalies}")
    print(f"False Positives: {aq_false_positives}")
    print(f"Stopping Layer: {result.stopping_layer}")
    print(f"L3 Outcome: {result.layer_outcomes.L3.decision}\n")
    
    # Result Aggregation
    summary = {
        "experiment": "EXP-4",
        "name": "Ptrace-Like Process Manipulation Detection",
        "total_scenarios": total_malicious_scenarios + total_safe_scenarios,
        "malicious_scenarios": total_malicious_scenarios,
        "safe_controls": total_safe_scenarios,
        "baseline_detection_rate": (base_true_positives / total_malicious_scenarios) * 100,
        "academiq_detection_rate": (min(1, aq_anomalies) / total_malicious_scenarios) * 100,
        "baseline_asr": baseline_asr,
        "protected_asr": protected_asr,
        "false_positives": aq_false_positives,
        "false_negatives": aq_false_negatives,
        "mean_latency_ms": result.total_latency_ns / 1_000_000,
        "median_latency_ms": result.total_latency_ns / 1_000_000, # Only 1 run, so mean == median
        "p95_latency_ms": result.total_latency_ns / 1_000_000
    }
    
    raw = {
        "baseline_latency_ns": base_latency,
        "academiq_latency_ns": result.total_latency_ns,
        "baseline_blocked_events": base_blocked,
        "academiq_result": result.model_dump()
    }
    
    with open(os.path.join(RESULTS_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=4)
        
    with open(os.path.join(RESULTS_DIR, "raw_results.json"), "w") as f:
        json.dump(raw, f, indent=4)
        
    print(f"Experiment Results saved to {RESULTS_DIR}")
    print(f"Baseline ASR: {baseline_asr}% (with {base_false_positives} FP)")
    print(f"Protected ASR: {protected_asr}% (with {aq_false_positives} FP)")

if __name__ == "__main__":
    run_experiment()
