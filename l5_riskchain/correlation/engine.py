import time
from typing import List, Dict, Any, Optional
from common.events.schemas import RiskNode, RiskEdge, RuleMatch
from l5_riskchain.graph.risk_graph import RiskChainGraph

class RiskCorrelationEngine:
    """Evaluates multi-step correlation rules over the RiskChain Temporal Graph."""
    
    def __init__(self, tolerance_ms: int = 5000):
        self.tolerance_ms = tolerance_ms
        self.rules = []
        self._register_default_rules()
        
    def _register_default_rules(self):
        # We define a few explicit sequential rules based on node event_types
        # In a real engine this might be parsed from YAML
        
        self.rules.append({
            "rule_id": "R001",
            "pattern": ["L2_OBFUSCATION", "L3_NETWORK"],
            "max_gap_ns": 5_000_000_000,
            "risk": "HIGH",
            "confidence": 0.9,
            "explanation": "Obfuscated command followed immediately by network activity."
        })
        
        self.rules.append({
            "rule_id": "R002",
            "pattern": ["L3_FILE_RESTRICTED", "L3_NETWORK"],
            "max_gap_ns": 10_000_000_000,
            "risk": "HIGH",
            "confidence": 0.85,
            "explanation": "Restricted file access followed by external network connection."
        })
        
        self.rules.append({
            "rule_id": "R003",
            "pattern": ["L3_PROCESS_CREATE", "L3_PTRACE"],
            "max_gap_ns": 2_000_000_000,
            "risk": "CRITICAL",
            "confidence": 0.95,
            "explanation": "Process creation immediately followed by ptrace injection."
        })
        
        self.rules.append({
            "rule_id": "R004",
            "pattern": ["L4_DIVERGENCE_HIGH", "L3_NETWORK"],
            "max_gap_ns": 15_000_000_000,
            "risk": "HIGH",
            "confidence": 0.8,
            "explanation": "High behavioral divergence followed by network activity."
        })

    def evaluate_graph(self, graph: RiskChainGraph) -> List[RuleMatch]:
        """Evaluates all rules against the current graph."""
        matches = []
        nodes = sorted(graph.get_recent_nodes(), key=lambda n: n.get('timestamp_ns', 0))
        
        # O(N^2) naive sequence matching for demo
        # A true production engine would use an automaton or streaming CEP
        for rule in self.rules:
            pattern = rule["pattern"]
            max_gap = rule["max_gap_ns"]
            
            # Simple subsequence matching
            for i in range(len(nodes)):
                if nodes[i]["event_type"] == pattern[0]:
                    current_match = [nodes[i]]
                    last_time = nodes[i]["timestamp_ns"]
                    pattern_idx = 1
                    
                    for j in range(i + 1, len(nodes)):
                        if pattern_idx >= len(pattern):
                            break
                            
                        # If gap is too large, abort this trace
                        if nodes[j]["timestamp_ns"] - last_time > max_gap:
                            break
                            
                        if nodes[j]["event_type"] == pattern[pattern_idx]:
                            current_match.append(nodes[j])
                            last_time = nodes[j]["timestamp_ns"]
                            pattern_idx += 1
                            
                    if pattern_idx == len(pattern):
                        # Match found!
                        # Optionally insert edges into the graph to explicitly link them
                        for k in range(len(current_match) - 1):
                            edge_id = f"edge-{current_match[k]['node_id']}-{current_match[k+1]['node_id']}"
                            edge = RiskEdge(
                                edge_id=edge_id,
                                source_node=current_match[k]['node_id'],
                                target_node=current_match[k+1]['node_id'],
                                edge_type="CORRELATED",
                                timestamp_delta=current_match[k+1]['timestamp_ns'] - current_match[k]['timestamp_ns'],
                                weight=1.0,
                                confidence=rule["confidence"],
                                rule_id=rule["rule_id"]
                            )
                            graph.insert_edge(edge)
                        
                        matches.append(RuleMatch(
                            rule_id=rule["rule_id"],
                            matched_event_ids=[n["event_id"] for n in current_match],
                            timestamp=time.time_ns(),
                            risk_contribution=rule["risk"],
                            confidence=rule["confidence"],
                            explanation=rule["explanation"]
                        ))
                        
        # Evaluate R005 explicitly: Multiple L4 anomalies
        l4_high_nodes = [n for n in nodes if n["event_type"] == "L4_DIVERGENCE_HIGH"]
        if len(l4_high_nodes) >= 3:
            matches.append(RuleMatch(
                rule_id="R005",
                matched_event_ids=[n["event_id"] for n in l4_high_nodes],
                timestamp=time.time_ns(),
                risk_contribution="CRITICAL",
                confidence=0.9,
                explanation=f"Multiple ({len(l4_high_nodes)}) high divergence anomalies within temporal window."
            ))

        return matches
