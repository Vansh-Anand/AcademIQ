import time
import uuid
import networkx as nx
from typing import Dict, List, Any, Optional

from common.events.schemas import RiskNode, RiskEdge, BaseEvent

class RiskChainGraph:
    """Temporal graph for multi-step attack correlation."""
    def __init__(self, agent_id: str, window_seconds: int = 30, max_nodes: int = 10000):
        self.agent_id = agent_id
        self.window_seconds = window_seconds
        self.max_nodes = max_nodes
        self.graph = nx.DiGraph()
        
        # Keep track of events by ID to avoid duplicates
        self._event_map: Dict[str, str] = {}
        
    def _cull_expired_nodes(self, current_time_ns: int):
        """Removes nodes outside the temporal window."""
        threshold = current_time_ns - (self.window_seconds * 1_000_000_000)
        nodes_to_remove = []
        
        for node_id, data in self.graph.nodes(data=True):
            if data.get('timestamp_ns', current_time_ns) < threshold:
                nodes_to_remove.append(node_id)
                
        for node_id in nodes_to_remove:
            # Clean up event map
            event_id = self.graph.nodes[node_id].get('event_id')
            if event_id and event_id in self._event_map:
                del self._event_map[event_id]
            self.graph.remove_node(node_id)
            
    def _enforce_size_limit(self):
        """Prevents unbounded memory growth."""
        if self.graph.number_of_nodes() > self.max_nodes:
            # Remove oldest nodes
            nodes = sorted(self.graph.nodes(data=True), key=lambda x: x[1].get('timestamp_ns', 0))
            nodes_to_remove = [n[0] for n in nodes[:(self.graph.number_of_nodes() - self.max_nodes)]]
            for node_id in nodes_to_remove:
                event_id = self.graph.nodes[node_id].get('event_id')
                if event_id and event_id in self._event_map:
                    del self._event_map[event_id]
                self.graph.remove_node(node_id)

    def insert_node(self, node: RiskNode) -> bool:
        """Inserts a new node into the graph if not duplicate."""
        if node.event_id in self._event_map:
            return False
            
        self._cull_expired_nodes(node.timestamp_ns)
        self.graph.add_node(
            node.node_id,
            node_id=node.node_id,
            event_id=node.event_id,
            event_type=node.event_type,
            timestamp_ns=node.timestamp_ns,
            agent_id=node.agent_id,
            session_id=node.session_id,
            trace_id=node.trace_id,
            risk_contribution=node.risk_contribution,
            severity=node.severity,
            confidence=node.confidence,
            resource_class=node.resource_class,
            process_class=node.process_class,
            network_class=node.network_class,
            source_layer=node.source_layer
        )
        self._event_map[node.event_id] = node.node_id
        self._enforce_size_limit()
        return True

    def insert_edge(self, edge: RiskEdge):
        """Inserts an edge between nodes."""
        if self.graph.has_node(edge.source_node) and self.graph.has_node(edge.target_node):
            self.graph.add_edge(
                edge.source_node, 
                edge.target_node,
                edge_id=edge.edge_id,
                edge_type=edge.edge_type,
                timestamp_delta=edge.timestamp_delta,
                weight=edge.weight,
                confidence=edge.confidence,
                rule_id=edge.rule_id
            )

    def get_attack_paths(self) -> List[List[Dict[str, Any]]]:
        """Extracts the most critical paths (chains of events)."""
        paths = []
        # Find roots (nodes with in-degree 0)
        roots = [n for n, d in self.graph.in_degree() if d == 0]
        
        for root in roots:
            for target in self.graph.nodes():
                if root != target and nx.has_path(self.graph, root, target):
                    # We could use all_simple_paths but that might explode, shortest path works for a sequence
                    try:
                        path_nodes = nx.shortest_path(self.graph, root, target)
                        if len(path_nodes) > 1: # Only paths of length > 1
                            path_data = [self.graph.nodes[n] for n in path_nodes]
                            paths.append(path_data)
                    except nx.NetworkXNoPath:
                        continue
                        
        # Sort paths by cumulative risk
        paths.sort(key=lambda p: sum(n.get('risk_contribution', 0.0) for n in p), reverse=True)
        return paths
        
    def get_recent_nodes(self) -> List[Dict[str, Any]]:
        return [data for _, data in self.graph.nodes(data=True)]

