import time
from typing import Dict, Optional
from common.events.schemas import AgentIdentity, ProcessIdentity

class AgentScopeManager:
    """
    Manages the mapping between AcademIQ monitored agents and their Linux cgroup identities.
    Ensures that L3 eBPF telemetry is only processed/attributed for correctly registered cgroups,
    satisfying the least-privilege telemetry requirement.
    """
    def __init__(self):
        self._agents: Dict[str, AgentIdentity] = {}
        self._cgroup_to_agent: Dict[int, str] = {}
        
    def register_agent(self, agent_id: str, cgroup_id: int, root_pid: int, container_id: Optional[str] = None) -> AgentIdentity:
        import uuid
        identity = AgentIdentity(
            event_id=f"evt-{uuid.uuid4()}",
            timestamp_ns=time.time_ns(),
            layer="L3",
            trace_id=f"trc-{uuid.uuid4()}",
            agent_id=agent_id,
            cgroup_id=cgroup_id,
            container_id=container_id,
            root_pid=root_pid,
            start_time_ns=time.time_ns(),
            policy_version="1.0"
        )
        self._agents[agent_id] = identity
        self._cgroup_to_agent[cgroup_id] = agent_id
        return identity
        
    def resolve_cgroup(self, cgroup_id: int) -> Optional[str]:
        """Returns the agent_id for a given cgroup_id if monitored."""
        return self._cgroup_to_agent.get(cgroup_id)
        
    def is_monitored(self, cgroup_id: int) -> bool:
        """Determines if the cgroup should be monitored by L3."""
        return cgroup_id in self._cgroup_to_agent
        
    def unregister_agent(self, agent_id: str):
        if agent_id in self._agents:
            cgroup_id = self._agents[agent_id].cgroup_id
            del self._cgroup_to_agent[cgroup_id]
            del self._agents[agent_id]
            
    def get_agent(self, agent_id: str) -> Optional[AgentIdentity]:
        return self._agents.get(agent_id)
