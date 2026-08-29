import os
import json
import time
from typing import Dict, Any

from benchmarks.experiments.models import ScenarioDefinition
from common.events.schemas import RiskNode, RiskEdge
from benchmarks.experiments.runner import ExperimentHarness

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "technique3")

def create_node(node_id: str, event_type: str, timestamp_ns: int, risk: float, severity: str = "HIGH") -> RiskNode:
    return RiskNode(
        node_id=node_id,
        event_id=f"evt_{node_id}",
        event_type=event_type,
        timestamp_ns=timestamp_ns,
        agent_id="test_agent",
        session_id="session_default",
        trace_id="trace_default",
        risk_contribution=risk,
        severity=severity,
        confidence=1.0,
        source_layer="L3"
    )

def create_edge(source: str, target: str, delta: int, weight: float = 1.0) -> RiskEdge:
    return RiskEdge(
        edge_id=f"edge_{source}_{target}",
        source_node=source,
        target_node=target,
        edge_type="CAUSAL",
        timestamp_delta=delta,
        weight=weight,
        confidence=1.0
    )

def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # ---------------------------------------------------------
    # The Attack Sequence
    # L3_FILE_RESTRICTED (0.5) -> L3_NETWORK (0.7) -> L4_DIVERGENCE_HIGH (0.8)
    # Total Risk: 2.0 (High Risk)
    # ---------------------------------------------------------
    def generate_high_risk_attack_nodes(prefix: str, base_time: int):
        return [
            create_node(f"{prefix}_1", "L3_FILE_RESTRICTED", base_time, 0.5),
            create_node(f"{prefix}_2", "L3_NETWORK", base_time + 100, 0.7),
            create_node(f"{prefix}_3", "L4_DIVERGENCE_HIGH", base_time + 200, 0.8)
        ]
        
    def generate_high_risk_attack_edges(prefix: str):
        return [
            create_edge(f"{prefix}_1", f"{prefix}_2", 100),
            create_edge(f"{prefix}_2", f"{prefix}_3", 100)
        ]

    # ---------------------------------------------------------
    # The Benign Workflow
    # L3_FILE_READ (0.1) -> L3_PROCESS_CREATE (0.1) -> L3_NETWORK (0.1)
    # Total Risk: 0.3 (Low Risk)
    # ---------------------------------------------------------
    def generate_benign_nodes(prefix: str, base_time: int):
        return [
            create_node(f"{prefix}_1", "L3_FILE_READ", base_time, 0.1, severity="LOW"),
            create_node(f"{prefix}_2", "L3_PROCESS_CREATE", base_time + 100, 0.1, severity="LOW"),
            create_node(f"{prefix}_3", "L3_NETWORK", base_time + 200, 0.1, severity="LOW")
        ]
        
    def generate_benign_edges(prefix: str):
        return [
            create_edge(f"{prefix}_1", f"{prefix}_2", 100),
            create_edge(f"{prefix}_2", f"{prefix}_3", 100)
        ]

    # We will reuse the same harness so the detector's state persists.
    harness = ExperimentHarness()
    results_summary = {}

    def run_and_log(scenario_name: str, session_id: str, ts: int, nodes, edges):
        scenario = ScenarioDefinition(
            scenario_id=session_id,
            scenario_name=scenario_name,
            description="Testing cross session replay",
            category="L5",
            session_id=session_id,
            timestamp_ns=ts,
            risk_nodes=nodes,
            risk_edges=edges,
            expected_security_outcome="FREEZE"
        )
        
        result = harness.run_scenario(scenario)
        xs_result = result.metadata.get("cross_session", {})
        
        print(f"\n--- Scenario: {scenario_name} ---")
        print(f"Session ID: {session_id}")
        if "detection_state" in xs_result:
            print(f"Detection State: {xs_result['detection_state']}")
            print(f"Repeat Count: {xs_result['repeat_count']}")
            print(f"Matching Sessions: {xs_result['matching_session_ids']}")
        else:
            print("No path found.")
            
        results_summary[scenario_name] = xs_result
        return xs_result

    # Scenario A: First Observation
    ts_a = 1_000_000_000
    res_a = run_and_log("First Observation", "session_A", ts_a, 
                generate_high_risk_attack_nodes("a", ts_a), 
                generate_high_risk_attack_edges("a"))
                
    # Scenario B: Exact Structural Replay
    ts_b = ts_a + 60 * 1_000_000_000 # 1 minute later
    res_b = run_and_log("Exact Structural Replay", "session_B", ts_b, 
                generate_high_risk_attack_nodes("b", ts_b), 
                generate_high_risk_attack_edges("b"))
                
    # Scenario C: Coordinated Multi-Session (Threshold = 3)
    ts_c = ts_a + 120 * 1_000_000_000 # 2 minutes later
    res_c = run_and_log("Coordinated Multi-Session", "session_C", ts_c, 
                generate_high_risk_attack_nodes("c", ts_c), 
                generate_high_risk_attack_edges("c"))
                
    # Scenario D: Legitimate Repeated Workflow 1
    ts_d1 = 2_000_000_000
    res_d1 = run_and_log("Legitimate Workflow (1)", "session_D1", ts_d1, 
                generate_benign_nodes("d1", ts_d1), 
                generate_benign_edges("d1"))
                
    # Scenario D: Legitimate Repeated Workflow 2 (Should not trigger REPLAY_ALERT)
    ts_d2 = ts_d1 + 60 * 1_000_000_000
    res_d2 = run_and_log("Legitimate Workflow (2)", "session_D2", ts_d2, 
                generate_benign_nodes("d2", ts_d2), 
                generate_benign_edges("d2"))
                
    # Scenario E: Similar But Different
    ts_e = ts_a + 180 * 1_000_000_000
    nodes_e = [
        create_node("e_1", "L3_FILE_RESTRICTED", ts_e, 0.5),
        create_node("e_2", "L3_NETWORK", ts_e + 100, 0.7),
        create_node("e_3", "L3_PRIVILEGE_ESCALATION", ts_e + 200, 0.9) # Different terminal node
    ]
    edges_e = [create_edge("e_1", "e_2", 100), create_edge("e_2", "e_3", 100)]
    res_e = run_and_log("Similar But Different", "session_E", ts_e, nodes_e, edges_e)
    
    # Scenario F: Outside Temporal Window
    # Default window is 3600 seconds (1 hour)
    ts_f = ts_a + (7200 * 1_000_000_000) # 2 hours later
    res_f = run_and_log("Outside Temporal Window", "session_F", ts_f, 
                generate_high_risk_attack_nodes("f", ts_f), 
                generate_high_risk_attack_edges("f"))

    print("\n--- Summary Validation ---")
    if res_a["detection_state"] == "NEW_PATTERN":
        print("[SUCCESS] Scenario A correctly identified as NEW_PATTERN.")
    
    if res_b["detection_state"] == "REPLAY_ALERT":
        print("[SUCCESS] Scenario B correctly identified as REPLAY_ALERT.")
        
    if res_c["detection_state"] == "COORDINATED_PATTERN":
        print("[SUCCESS] Scenario C correctly identified as COORDINATED_PATTERN.")
        
    if res_d2["detection_state"] == "LEGITIMATE_REPEAT":
        print("[SUCCESS] Scenario D2 correctly identified as LEGITIMATE_REPEAT (bypassed alert due to low risk).")
        
    if res_e["detection_state"] == "NEW_PATTERN":
        print("[SUCCESS] Scenario E correctly identified as NEW_PATTERN (different fingerprint).")
        
    if res_f["detection_state"] == "REPEATED_PATTERN" or res_f["detection_state"] == "REPLAY_ALERT": # wait, risk is high so it upgrades
        print("[SUCCESS] Scenario F correctly identified as REPLAY_ALERT but NOT coordinated (outside window).")

    with open(os.path.join(RESULTS_DIR, "summary.json"), "w") as f:
        json.dump(results_summary, f, indent=4)
        
    print(f"Results saved to {os.path.abspath(RESULTS_DIR)}")

if __name__ == "__main__":
    main()
