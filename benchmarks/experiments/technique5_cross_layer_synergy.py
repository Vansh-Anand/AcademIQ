import os
import sys
import json
import time
import uuid
import statistics

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from benchmarks.experiments.models import ScenarioDefinition
from benchmarks.experiments.runner import ExperimentHarness
from common.events.schemas import SyscallEvent
from l2_sdn.events import NormalizedCommandEvent
from common.schemas.security import DecisionEnum
from l3_ebpf.userspace.correlation import ExecutionCorrelationManager

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "technique5")
os.makedirs(RESULTS_DIR, exist_ok=True)

def evaluate_condition(condition_name: str, payload: dict, normalize: bool):
    """
    Evaluates a payload under a specific condition (RAW or NORMALIZED).
    Uses the CorrelationManager directly to isolate L3 logic.
    """
    correlation_manager = ExecutionCorrelationManager(time_window_ns=5_000_000_000)
    
    agent_id = "test_agent_1"
    
    # Simulate L2 Processing
    if normalize:
        from l2_sdn.interceptor import DevelopmentShellInterceptor
        from common.events.schemas import ShellCommandEvent
        
        interceptor = DevelopmentShellInterceptor()
        shell_evt = ShellCommandEvent(
            event_id=f"evt-{uuid.uuid4()}",
            agent_id=agent_id,
            trace_id="trace1",
            layer="AGENT",
            timestamp_ns=time.time_ns(),
            raw_command=payload["raw_command"]
        )
        decision, l2_event = interceptor.intercept(shell_evt)
        # If L2 blocks it, we don't even reach L3.
        # But for the sake of the A/B test of L3 false positives, we want to see how L3 reacts.
        # If L2 blocked a benign command, that's an L2 false positive. 
        # But we assume L2 allows benign commands.
        if decision == "ALLOW":
            correlation_manager.register_l2_decision(l2_event)
    else:
        # RAW condition: L2 just passes the raw text without normalization
        l2_event = NormalizedCommandEvent(
            event_id=f"evt-{uuid.uuid4()}",
            session_id="sess1",
            trace_id="trace1",
            layer="L2",
            timestamp_ns=time.time_ns(),
            agent_id=agent_id,
            original_command_hash="raw",
            canonical_command_hash="raw",
            command_text=payload["raw_command"], # Just the raw text!
            policy_result="ALLOW",
            security_decision="ALLOW"
        )
        # We manually register the raw allowance
        correlation_manager.register_l2_decision(l2_event)
        decision = "ALLOW"

    if decision == "BLOCK":
        return "BLOCK", 0 # Blocked by L2

    start_ns = time.perf_counter_ns()
    
    # Simulate L3 Syscall Event
    syscall_event = SyscallEvent(
        event_id=f"sys-{uuid.uuid4()}",
        trace_id="trace1",
        layer="L3",
        timestamp_ns=time.time_ns(),
        agent_id=agent_id,
        pid=1002,
        syscall_name="execve",
        executable=payload["syscall_executable"],
        arguments={"args": payload["syscall_arguments"]},
        cgroup_id=1000
    )
    
    correlated, anomaly = correlation_manager.correlate_syscall(syscall_event)
    
    end_ns = time.perf_counter_ns()
    latency_ns = end_ns - start_ns
    
    # If not correlated, it's an anomaly -> blocked by L3
    if not correlated:
        return "BLOCK", latency_ns
    return "ALLOW", latency_ns

def run_experiment():
    payloads = [
        {
            "id": "scenario_1",
            "category": "Plain Benign Command",
            "raw_command": "cat /tmp/safe.txt",
            "syscall_executable": "cat",
            "syscall_arguments": ["/tmp/safe.txt"],
            "ground_truth": "BENIGN"
        },
        {
            "id": "scenario_2",
            "category": "Benign Path Representation Variation",
            "raw_command": "cat /tmp/././safe.txt",
            "syscall_executable": "cat",
            "syscall_arguments": ["/tmp/safe.txt"],
            "ground_truth": "BENIGN"
        },
        {
            "id": "scenario_3",
            "category": "Benign Path Traversal Representation",
            "raw_command": "cat /tmp/../tmp/safe.txt",
            "syscall_executable": "cat",
            "syscall_arguments": ["/tmp/safe.txt"],
            "ground_truth": "BENIGN"
        },
        {
            "id": "scenario_4",
            "category": "Malicious Plain Command",
            "raw_command": "rm -rf /etc/passwd",
            "syscall_executable": "rm",
            "syscall_arguments": ["-rf", "/etc/passwd"],
            "ground_truth": "MALICIOUS"
        },
        {
            "id": "scenario_5",
            "category": "Malicious Obfuscated Command",
            "raw_command": "r\\m -r\\f /etc/passwd",
            "syscall_executable": "rm",
            "syscall_arguments": ["-rf", "/etc/passwd"],
            "ground_truth": "MALICIOUS"
        },
        {
            "id": "scenario_6",
            "category": "Authorization Correlation Mismatch",
            "raw_command": "c'a't /t'm'p/safe.txt",
            "syscall_executable": "cat",
            "syscall_arguments": ["/tmp/safe.txt"],
            "ground_truth": "BENIGN"
        }
    ]
    
    raw_results = []
    
    metrics = {
        "raw_l3_only": {"total": 0, "tp": 0, "tn": 0, "fp": 0, "fn": 0},
        "sdn_normalized_l3": {"total": 0, "tp": 0, "tn": 0, "fp": 0, "fn": 0},
        "latencies": {"raw": [], "normalized": []}
    }
    
    for p in payloads:
        print(f"\n--- {p['id']}: {p['category']} ---")
        
        # Condition A: RAW
        raw_decision, raw_lat = evaluate_condition("RAW_L3_ONLY", p, normalize=False)
        # Condition B: NORMALIZED
        norm_decision, norm_lat = evaluate_condition("SDN_NORMALIZED_L3", p, normalize=True)
        
        metrics["latencies"]["raw"].append(raw_lat)
        metrics["latencies"]["normalized"].append(norm_lat)
        
        raw_fp = (p["ground_truth"] == "BENIGN" and raw_decision == "BLOCK")
        raw_fn = (p["ground_truth"] == "MALICIOUS" and raw_decision == "ALLOW")
        raw_tp = (p["ground_truth"] == "MALICIOUS" and raw_decision == "BLOCK")
        raw_tn = (p["ground_truth"] == "BENIGN" and raw_decision == "ALLOW")
        
        norm_fp = (p["ground_truth"] == "BENIGN" and norm_decision == "BLOCK")
        norm_fn = (p["ground_truth"] == "MALICIOUS" and norm_decision == "ALLOW")
        norm_tp = (p["ground_truth"] == "MALICIOUS" and norm_decision == "BLOCK")
        norm_tn = (p["ground_truth"] == "BENIGN" and norm_decision == "ALLOW")
        
        metrics["raw_l3_only"]["total"] += 1
        metrics["raw_l3_only"]["fp"] += int(raw_fp)
        metrics["raw_l3_only"]["fn"] += int(raw_fn)
        metrics["raw_l3_only"]["tp"] += int(raw_tp)
        metrics["raw_l3_only"]["tn"] += int(raw_tn)
        
        metrics["sdn_normalized_l3"]["total"] += 1
        metrics["sdn_normalized_l3"]["fp"] += int(norm_fp)
        metrics["sdn_normalized_l3"]["fn"] += int(norm_fn)
        metrics["sdn_normalized_l3"]["tp"] += int(norm_tp)
        metrics["sdn_normalized_l3"]["tn"] += int(norm_tn)
        
        raw_results.append({
            "scenario_id": p["id"],
            "category": p["category"],
            "raw_command": p["raw_command"],
            "ground_truth": p["ground_truth"],
            "raw_l3_decision": raw_decision,
            "normalized_l3_decision": norm_decision,
            "raw_latency_ns": raw_lat,
            "normalized_latency_ns": norm_lat,
            "whether_raw_was_false_positive": raw_fp,
            "whether_normalized_was_false_positive": norm_fp
        })
        
        print(f"Ground Truth: {p['ground_truth']}")
        print(f"RAW L3 Decision: {raw_decision}")
        print(f"NORMALIZED L3 Decision: {norm_decision}")
        
    for k in ["raw_l3_only", "sdn_normalized_l3"]:
        fp = metrics[k]["fp"]
        tn = metrics[k]["tn"]
        tp = metrics[k]["tp"]
        fn = metrics[k]["fn"]
        
        metrics[k]["false_positive_rate"] = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        metrics[k]["detection_rate"] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        metrics[k]["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        metrics[k]["recall"] = metrics[k]["detection_rate"]
        metrics[k]["f1"] = 2 * (metrics[k]["precision"] * metrics[k]["recall"]) / (metrics[k]["precision"] + metrics[k]["recall"]) if (metrics[k]["precision"] + metrics[k]["recall"]) > 0 else 0.0

    fpr_raw = metrics["raw_l3_only"]["false_positive_rate"]
    fpr_norm = metrics["sdn_normalized_l3"]["false_positive_rate"]
    
    fpr_red_abs = fpr_raw - fpr_norm
    if fpr_raw > 0:
        fpr_red_pct = (fpr_red_abs / fpr_raw) * 100
    else:
        fpr_red_pct = None
        
    summary = {
        "technique": "sdn_l3_cross_layer_false_positive_reduction",
        "raw_l3_only": {k: v for k, v in metrics["raw_l3_only"].items()},
        "sdn_normalized_l3": {k: v for k, v in metrics["sdn_normalized_l3"].items()},
        "false_positive_reduction": {
            "absolute": fpr_red_abs,
            "percentage": fpr_red_pct
        },
        "latency": {
            "raw": {
                "mean": statistics.mean(metrics["latencies"]["raw"]) / 1_000_000 if metrics["latencies"]["raw"] else 0,
                "median": statistics.median(metrics["latencies"]["raw"]) / 1_000_000 if metrics["latencies"]["raw"] else 0
            },
            "normalized": {
                "mean": statistics.mean(metrics["latencies"]["normalized"]) / 1_000_000 if metrics["latencies"]["normalized"] else 0,
                "median": statistics.median(metrics["latencies"]["normalized"]) / 1_000_000 if metrics["latencies"]["normalized"] else 0
            }
        },
        "limitations": [
            "Simulation-based L3 telemetry",
            "Limited corpus size (6 deterministic scenarios)",
            "Absence of live eBPF matching"
        ]
    }
    
    with open(os.path.join(RESULTS_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=4)
        
    with open(os.path.join(RESULTS_DIR, "raw_results.json"), "w") as f:
        json.dump(raw_results, f, indent=4)
        
    print("\n--- EXPERIMENT SUMMARY ---")
    print(f"RAW FPR: {fpr_raw*100:.2f}%")
    print(f"NORMALIZED FPR: {fpr_norm*100:.2f}%")
    
    if fpr_red_pct is not None:
        print(f"False Positive Reduction: {fpr_red_pct:.2f}%")
    else:
        print("No measurable false-positive reduction because the baseline produced zero false positives.")
        
if __name__ == "__main__":
    run_experiment()
