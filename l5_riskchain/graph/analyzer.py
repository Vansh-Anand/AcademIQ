import networkx as nx
from typing import Dict, List, Any, Optional
from l5_riskchain.graph.risk_graph import RiskChainGraph
from l6_eces.crypto.hasher import HashProvider

class RiskPathAnalyzer:
    """Analyzes RiskChainGraph to extract the highest-risk causal attack chain."""
    
    def __init__(self):
        self.hasher = HashProvider()

    def analyze(self, graph: RiskChainGraph) -> Optional[Dict[str, Any]]:
        """
        Finds the highest-risk causal path using DAG maximum weight path optimization.
        """
        nx_graph = graph.graph
        if nx_graph.number_of_nodes() == 0:
            return None
            
        if not nx.is_directed_acyclic_graph(nx_graph):
            paths = graph.get_attack_paths()
            if not paths:
                return None
            best_path_data = paths[0]
        else:
            try:
                topo_order = list(nx.topological_sort(nx_graph))
            except nx.NetworkXUnfeasible:
                return None
                
            dp = {node: (nx_graph.nodes[node].get('risk_contribution', 0.0), [node]) for node in topo_order}
            
            for node in topo_order:
                for neighbor in nx_graph.successors(node):
                    neighbor_risk = nx_graph.nodes[neighbor].get('risk_contribution', 0.0)
                    new_risk = dp[node][0] + neighbor_risk
                    
                    if new_risk > dp[neighbor][0]:
                        dp[neighbor] = (new_risk, dp[node][1] + [neighbor])
                        
            best_node = max(dp.keys(), key=lambda n: dp[n][0])
            best_risk, best_path = dp[best_node]
            
            best_path_data = [nx_graph.nodes[n] for n in best_path]
            
        return self._build_result(best_path_data)
        
    def _build_result(self, path_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not path_data:
            return None
            
        risk_score = sum(n.get('risk_contribution', 0.0) for n in path_data)
        
        signature = self.generate_signature(path_data)
        fingerprint = self.generate_fingerprint(signature)
        
        causally_valid = True
        for i in range(1, len(path_data)):
            if path_data[i-1].get('timestamp_ns', 0) >= path_data[i].get('timestamp_ns', 0):
                causally_valid = False
                break
                
        return {
            "path": [n.get('event_type', 'UNKNOWN') for n in path_data],
            "raw_nodes": path_data,
            "risk_score": risk_score,
            "signature": signature,
            "fingerprint": fingerprint,
            "causally_valid": causally_valid
        }
        
    def generate_signature(self, path_data: List[Dict[str, Any]]) -> str:
        """Generates a deterministic semantic sequence string."""
        return "->".join(n.get('event_type', 'UNKNOWN') for n in path_data)
        
    def generate_fingerprint(self, signature: str) -> str:
        """Hashes the signature using ECES infrastructure."""
        return self.hasher.hash(signature.encode("utf-8"))
