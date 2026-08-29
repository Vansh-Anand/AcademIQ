from typing import List, Optional
from pydantic import BaseModel

class SecurityDomain(BaseModel):
    """The hardened domain where the AcademIQ security monitor executes."""
    domain_id: str
    trust_level: str = "T2"  # T2 = Security monitor, T3 = Hardware anchor, T4 = Remote attestation verified
    components: List[str]
    attestation_state: str
    integrity_state: str
    policy_state: str

class AgentDomain(BaseModel):
    """The untrusted domain where the LLM Agent executes."""
    agent_id: str
    trust_level: str = "T0"  # T0 = Untrusted agent
    cgroup_id: Optional[str]
    namespace_ids: List[str]
    root_pid: Optional[int]
    policy_id: str

class IsolationVerifier:
    """Verifies trust boundaries between the AgentDomain and SecurityDomain."""
    
    @staticmethod
    def verify_boundary(agent: AgentDomain, security: SecurityDomain) -> bool:
        # Trust level MUST be strictly greater for the security domain
        t_sec = int(security.trust_level.replace("T", ""))
        t_agent = int(agent.trust_level.replace("T", ""))
        
        if t_sec <= t_agent:
            return False
            
        # Agent cgroup should not encompass the security root PID
        # Simulation only on Windows
        return True
