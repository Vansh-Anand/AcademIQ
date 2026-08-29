import os
import sys
import time
import json
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from common.events.schemas import RiskNode, RiskEdge
from benchmarks.experiments.models import ScenarioDefinition
from benchmarks.experiments.runner import ExperimentHarness
from common.schemas.security import DecisionEnum

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "technique2")
os.makedirs(RESULTS_DIR, exist_ok=True)

def create_node(node_id: str, event_type: str, ts_offset: int, risk: float) -> RiskNode:
    return RiskNode(
        node_id=node_id,
        event_id=f"evt-{node_id}",
        event_type=event_type,
        timestamp_ns=1000000000 + ts_offset,
        agent_id="test_agent",
        session_id="s1",
        trace_id="t1",
        risk_contribution=risk,
        severity="HIGH" if risk > 0.5 else "MEDIUM",
        confidence=1.0,
        source_layer="L3"
    )

def create_edge(source: str, target: str, ts_delta: int) -> RiskEdge:
    return RiskEdge(
        edge_id=f"edge-{source}-{target}",
        source_node=source,
        target_node=target,
        edge_type="CAUSAL",
        timestamp_delta=ts_delta,
        weight=1.0,
        confidence=1.0,
        rule_id="CAUSAL_SEQ"
    )

def build_scenarios():
    scenarios = []
    
    # SCENARIO A: Full Exfiltration Chain
    n1 = create_node("n1", "L3_FILE_RESTRICTED", 0, 0.4)
    n2 = create_node("n2", "L3_NETWORK", 100, 0.6)
    n3 = create_node("n3", "L4_DIVERGENCE_HIGH", 200, 0.9)
    nodes_a = [n1, n2, n3]
    edges_a = [
        create_edge("n1", "n2", 100),
        create_edge("n2", "n3", 100)
    ]
    scenarios.append(ScenarioDefinition(
        scenario_id="EXP-T2-A",
        scenario_name="Full Exfiltration",
        description="Valid causal path",
        category="path_analysis",
        risk_nodes=nodes_a,
        risk_edges=edges_a,
        expected_security_outcome=DecisionEnum.BLOCK
    ))
    
    # SCENARIO B: Competing Paths
    b_n1 = create_node("b1", "L2_OBFUSCATION", 0, 0.5)
    b_n2 = create_node("b2", "L3_PROCESS_CREATE", 50, 0.1)
    b_n3 = create_node("b3", "L3_NETWORK", 100, 0.2)
    
    b_n4 = create_node("b4", "L3_PTRACE", 150, 0.8)
    b_n5 = create_node("b5", "L4_DIVERGENCE_HIGH", 200, 0.9)
    
    nodes_b = [b_n1, b_n2, b_n3, b_n4, b_n5]
    edges_b = [
        create_edge("b1", "b2", 100),
        create_edge("b2", "b3", 50),
        create_edge("b1", "b4", 100),
        create_edge("b4", "b5", 50)
    ]
    scenarios.append(ScenarioDefinition(
        scenario_id="EXP-T2-B",
        scenario_name="Competing Paths",
        description="Should select the highest risk sequence",
        category="path_analysis",
        risk_nodes=nodes_b,
        risk_edges=edges_b,
        expected_security_outcome=DecisionEnum.BLOCK
    ))

    # SCENARIO C: Reversed Causal Order
    c_n1 = create_node("c1", "L3_FILE_RESTRICTED", 200, 0.4)
    c_n2 = create_node("c2", "L3_NETWORK", 100, 0.6)
    nodes_c = [c_n1, c_n2]
    edges_c = [
        create_edge("c1", "c2", -100)
    ]
    scenarios.append(ScenarioDefinition(
        scenario_id="EXP-T2-C",
        scenario_name="Reversed Causal Order",
        description="Path has invalid causality",
        category="path_analysis",
        risk_nodes=nodes_c,
        risk_edges=edges_c,
        expected_security_outcome=DecisionEnum.ALLOW
    ))
    
    # SCENARIO D: Partial Chain
    d_n1 = create_node("d1", "L3_FILE_RESTRICTED", 0, 0.3)
    d_n2 = create_node("d2", "L3_PROCESS_CREATE", 100, 0.2)
    nodes_d = [d_n1, d_n2]
    edges_d = [create_edge("d1", "d2", 100)]
    scenarios.append(ScenarioDefinition(
        scenario_id="EXP-T2-D",
        scenario_name="Partial Chain",
        description="Lower risk than full chain",
        category="path_analysis",
        risk_nodes=nodes_d,
        risk_edges=edges_d,
        expected_security_outcome=DecisionEnum.ALLOW
    ))
    
    # SCENARIO E: Structurally Equivalent
    e_n1 = create_node("e1", "L3_FILE_RESTRICTED", 500, 0.4)
    e_n2 = create_node("e2", "L3_NETWORK", 600, 0.6)
    e_n3 = create_node("e3", "L4_DIVERGENCE_HIGH", 700, 0.9)
    nodes_e = [e_n1, e_n2, e_n3]
    edges_e = [
        create_edge("e1", "e2", 100),
        create_edge("e2", "e3", 100)
    ]
    scenarios.append(ScenarioDefinition(
        scenario_id="EXP-T2-E",
        scenario_name="Structurally Equivalent",
        description="Should yield identical fingerprint to Scenario A",
        category="path_analysis",
        risk_nodes=nodes_e,
        risk_edges=edges_e,
        expected_security_outcome=DecisionEnum.BLOCK
    ))

    return scenarios

def main():
    harness = ExperimentHarness()
    scenarios = build_scenarios()
    
    results_summary = []
    fingerprints = {}
    
    for s in scenarios:
        print(f"\n--- Scenario: {s.scenario_name} ---")
        result = harness.run_scenario(s)
        
        meta = result.metadata
        path_analysis = meta.get("path_analysis")
        
        causally_valid = False
        signature = None
        fingerprint = None
        risk_score = 0.0
        
        if path_analysis:
            causally_valid = path_analysis.get("causally_valid", False)
            signature = path_analysis.get("signature")
            fingerprint = path_analysis.get("fingerprint")
            risk_score = path_analysis.get("risk_score", 0.0)
            print(f"Path Signature: {signature}")
            print(f"Fingerprint: {fingerprint}")
            print(f"Risk Score: {risk_score}")
            print(f"Causally Valid: {causally_valid}")
            
            fingerprints[s.scenario_id] = fingerprint
        else:
            print("No path found.")
            
        results_summary.append({
            "scenario_id": s.scenario_id,
            "name": s.scenario_name,
            "has_path": path_analysis is not None,
            "causally_valid": causally_valid,
            "signature": signature,
            "fingerprint": fingerprint,
            "risk_score": risk_score
        })
        
    fp_a = fingerprints.get("EXP-T2-A")
    fp_e = fingerprints.get("EXP-T2-E")
    
    print("\n--- Summary ---")
    if fp_a and fp_e and fp_a == fp_e:
        print("[SUCCESS] Structural Equivalence Verified: Fingerprint A matches Fingerprint E.")
    else:
        print("[FAILURE] Structural Equivalence Failed.")
        
    with open(os.path.join(RESULTS_DIR, "summary.json"), "w") as f:
        json.dump(results_summary, f, indent=4)
        
    print(f"Results saved to {RESULTS_DIR}")

if __name__ == "__main__":
    main()
