import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from l5_riskchain.graph.risk_graph import RiskChainGraph
from l5_riskchain.graph.analyzer import RiskPathAnalyzer
from common.events.schemas import RiskNode, RiskEdge

def test_dag_longest_path_max_flow():
    graph = RiskChainGraph(agent_id="test")
    analyzer = RiskPathAnalyzer()
    
    n1 = RiskNode(node_id="1", event_id="e1", event_type="A", timestamp_ns=1000, agent_id="test", session_id="s", trace_id="t", risk_contribution=0.1, severity="LOW", confidence=1.0, source_layer="L3")
    n2 = RiskNode(node_id="2", event_id="e2", event_type="B", timestamp_ns=2000, agent_id="test", session_id="s", trace_id="t", risk_contribution=0.2, severity="LOW", confidence=1.0, source_layer="L3")
    n3 = RiskNode(node_id="3", event_id="e3", event_type="C", timestamp_ns=3000, agent_id="test", session_id="s", trace_id="t", risk_contribution=0.8, severity="HIGH", confidence=1.0, source_layer="L3")
    n4 = RiskNode(node_id="4", event_id="e4", event_type="D", timestamp_ns=4000, agent_id="test", session_id="s", trace_id="t", risk_contribution=0.9, severity="HIGH", confidence=1.0, source_layer="L3")
    
    graph.insert_node(n1)
    graph.insert_node(n2)
    graph.insert_node(n3)
    graph.insert_node(n4)
    
    # Path 1: 1 -> 2 -> 3 (Risk: 0.1+0.2+0.8 = 1.1)
    # Path 2: 1 -> 4 (Risk: 0.1+0.9 = 1.0)
    
    graph.insert_edge(RiskEdge(edge_id="e_1_2", source_node="1", target_node="2", edge_type="C", timestamp_delta=1000, weight=1.0, confidence=1.0, rule_id="R"))
    graph.insert_edge(RiskEdge(edge_id="e_2_3", source_node="2", target_node="3", edge_type="C", timestamp_delta=1000, weight=1.0, confidence=1.0, rule_id="R"))
    graph.insert_edge(RiskEdge(edge_id="e_1_4", source_node="1", target_node="4", edge_type="C", timestamp_delta=3000, weight=1.0, confidence=1.0, rule_id="R"))
    
    result = analyzer.analyze(graph)
    assert result is not None
    assert result["risk_score"] == 1.1
    assert result["signature"] == "A->B->C"
    
def test_causal_validation_failure():
    graph = RiskChainGraph(agent_id="test")
    analyzer = RiskPathAnalyzer()
    
    # n2 is before n1 temporally
    n1 = RiskNode(node_id="1", event_id="e1", event_type="A", timestamp_ns=2000, agent_id="test", session_id="s", trace_id="t", risk_contribution=0.1, severity="LOW", confidence=1.0, source_layer="L3")
    n2 = RiskNode(node_id="2", event_id="e2", event_type="B", timestamp_ns=1000, agent_id="test", session_id="s", trace_id="t", risk_contribution=0.2, severity="LOW", confidence=1.0, source_layer="L3")
    
    graph.insert_node(n1)
    graph.insert_node(n2)
    
    # Malicious or buggy edge claiming 1 -> 2
    graph.insert_edge(RiskEdge(edge_id="e_1_2", source_node="1", target_node="2", edge_type="C", timestamp_delta=-1000, weight=1.0, confidence=1.0, rule_id="R"))
    
    result = analyzer.analyze(graph)
    assert result is not None
    assert result["causally_valid"] is False

def test_fingerprint_determinism():
    analyzer = RiskPathAnalyzer()
    fp1 = analyzer.generate_fingerprint("A->B->C")
    fp2 = analyzer.generate_fingerprint("A->B->C")
    fp3 = analyzer.generate_fingerprint("A->B->D")
    
    assert fp1 == fp2
    assert fp1 != fp3
