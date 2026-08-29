import os
import sys
import time
import json
import uuid
import statistics

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from common.events.schemas import RiskNode
from benchmarks.experiments.models import ScenarioDefinition
from benchmarks.experiments.runner import ExperimentHarness

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "exp3")
os.makedirs(RESULTS_DIR, exist_ok=True)

def create_node(event_type: str, ts_offset: int) -> RiskNode:
    return RiskNode(
        node_id=f"node-{uuid.uuid4()}",
        event_id=f"evt-{uuid.uuid4()}",
        event_type=event_type,
        timestamp_ns=time.time_ns() + ts_offset,
        agent_id="test_agent",
        session_id="s1",
        trace_id="t1",
        risk_contribution=0.2, # default
        severity="MEDIUM",
        confidence=1.0,
        source_layer="L3"
    )

def baseline_evaluate(nodes):
    """
    Baseline methodology: evaluates each event independently.
    If ANY event is CRITICAL severity by itself, it blocks.
    Otherwise, allows. No temporal correlation.
    """
    for n in nodes:
        if n.severity == "CRITICAL":
            return True
    return False

def build_scenarios():
    scenarios = []
    
    # SCENARIO A: SAFE FILE READ
    # Single safe read
    nodes_a = [create_node("L3_FILE_RESTRICTED", 0)]
    # File read is MEDIUM severity typically (or low), so baseline ALLOWS.
    scenarios.append({
        "id": "A",
        "name": "Safe File Read",
        "nodes": nodes_a,
        "is_attack": False,
        "expected_l5": "ALLOW" # Or WARN
    })
    
    # SCENARIO B: SAFE NETWORK ACTIVITY
    nodes_b = [create_node("L3_NETWORK", 0)]
    scenarios.append({
        "id": "B",
        "name": "Safe Network Activity",
        "nodes": nodes_b,
        "is_attack": False,
        "expected_l5": "ALLOW"
    })
    
    # SCENARIO C: TEMPORALLY SEPARATED EVENTS
    # Assuming window is 5000ms (5 seconds). We separate by 10s.
    nodes_c = [
        create_node("L3_FILE_RESTRICTED", 0),
        create_node("L3_NETWORK", 10_000_000_000) # 10 seconds later
    ]
    scenarios.append({
        "id": "C",
        "name": "Temporally Separated Events",
        "nodes": nodes_c,
        "is_attack": False,
        "expected_l5": "ALLOW"
    })
    
    # SCENARIO D: MULTI-STEP EXFILTRATION ATTACK
    nodes_d = [
        create_node("L3_FILE_RESTRICTED", 0),
        create_node("L3_NETWORK", 1_000_000_000), # 1 second later
        create_node("L4_DIVERGENCE_HIGH", 2_000_000_000) # Exfiltration behavior marker
    ]
    scenarios.append({
        "id": "D",
        "name": "Multi-Step Exfiltration Chain",
        "nodes": nodes_d,
        "is_attack": True,
        "expected_l5": "BLOCK" # Will map to FREEZE in Governance
    })
    
    # SCENARIO E: PARTIAL CHAIN
    nodes_e = [
        create_node("L3_FILE_RESTRICTED", 0),
        create_node("L4_DIVERGENCE_HIGH", 1_000_000_000)
    ]
    scenarios.append({
        "id": "E",
        "name": "Partial Chain",
        "nodes": nodes_e,
        "is_attack": False,
        "expected_l5": "ALLOW"
    })
    
    # SCENARIO F: REVERSED ORDER CONTROL
    nodes_f = [
        create_node("L3_NETWORK", 0),
        create_node("L3_FILE_RESTRICTED", 1_000_000_000)
    ]
    scenarios.append({
        "id": "F",
        "name": "Reversed Order Control",
        "nodes": nodes_f,
        "is_attack": False,
        "expected_l5": "ALLOW"
    })
    
    return scenarios

def main():
    harness = ExperimentHarness()
    scenarios = build_scenarios()
    
    raw_results = []
    
    baseline_detections = 0
    baseline_misses = 0
    l5_detections = 0
    l5_misses = 0
    
    latencies = []
    total_attack = sum(1 for s in scenarios if s["is_attack"])
    total_safe = len(scenarios) - total_attack
    
    gov_distribution = {"ALLOW": 0, "WARN": 0, "THROTTLE": 0, "FREEZE": 0, "BLOCK": 0}
    
    print("Running EXP-3: Multi-Step Exfiltration Chain")
    
    for s in scenarios:
        print(f"\n--- Scenario {s['id']}: {s['name']} ---")
        
        # 1. Baseline Evaluation
        baseline_blocked = baseline_evaluate(s["nodes"])
        
        # 2. L5 Evaluation
        scenario_def = ScenarioDefinition(
            scenario_id=f"EXP3-{s['id']}",
            scenario_name=s["name"],
            description="Testing Temporal Exfiltration Chain",
            category="exfiltration",
            risk_nodes=s["nodes"],
            expected_security_outcome="BLOCK" if s["is_attack"] else "ALLOW"
        )
        
        result = harness.run_scenario(scenario_def)
        l5_blocked = result.attack_blocked
        latencies.append(result.total_latency_ns)
        
        meta = result.metadata
        gov_dec = meta.get("gov_decision", {}).get("decision", "ALLOW")
        gov_distribution[gov_dec] = gov_distribution.get(gov_dec, 0) + 1
        
        if s["is_attack"]:
            if baseline_blocked:
                baseline_detections += 1
            else:
                baseline_misses += 1
                
            if l5_blocked:
                l5_detections += 1
            else:
                l5_misses += 1
        
        print(f"Baseline Blocked: {baseline_blocked}")
        print(f"L5 Blocked: {l5_blocked} (Governance: {gov_dec})")
        print(f"Bayesian Risk: {meta.get('b_result', {}).get('attack_probability', 0)}")
        print(f"Chain Severity: {meta.get('chain_score', 0)}")
        if result.errors:
            print(f"Errors: {result.errors}")
        
        raw_results.append({
            "scenario_id": s["id"],
            "name": s["name"],
            "is_attack": s["is_attack"],
            "baseline_detected": baseline_blocked,
            "l5_detected": l5_blocked,
            "governance_decision": gov_dec,
            "bayesian_probability": meta.get('b_result', {}).get('attack_probability', 0),
            "chain_score": meta.get('chain_score', 0),
            "graph_nodes": meta.get('graph_stats', {}).get('nodes', 0),
            "graph_edges": meta.get('graph_stats', {}).get('edges', 0),
            "latency_ms": result.total_latency_ns / 1_000_000
        })

    baseline_asr = (baseline_misses / total_attack) * 100 if total_attack else 0
    protected_asr = (l5_misses / total_attack) * 100 if total_attack else 0
    detection_rate = (l5_detections / total_attack) * 100 if total_attack else 0
    
    summary = {
        "experiment": "EXP-3",
        "total_scenarios": len(scenarios),
        "attack_scenarios": total_attack,
        "safe_scenarios": total_safe,
        "baseline": {
            "detections": baseline_detections,
            "misses": baseline_misses,
            "attack_success_rate": baseline_asr
        },
        "l5_riskchain": {
            "detections": l5_detections,
            "misses": l5_misses,
            "attack_success_rate": protected_asr,
            "detection_rate": detection_rate,
            "false_negatives": l5_misses,
            "false_positives": sum(1 for r in raw_results if not r["is_attack"] and r["l5_detected"])
        },
        "governance_distribution": gov_distribution,
        "latency_ms": {
            "mean": statistics.mean(latencies) / 1_000_000,
            "median": statistics.median(latencies) / 1_000_000,
            "p95": statistics.quantiles(latencies, n=100)[94] / 1_000_000 if len(latencies) > 1 else latencies[0] / 1_000_000
        }
    }
    
    with open(os.path.join(RESULTS_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=4)
        
    with open(os.path.join(RESULTS_DIR, "raw_results.json"), "w") as f:
        json.dump(raw_results, f, indent=4)
        
    print(f"\nExperiment Results saved to {RESULTS_DIR}")
    print(f"Baseline ASR: {baseline_asr}%")
    print(f"L5 Protected ASR: {protected_asr}%")

if __name__ == "__main__":
    main()
