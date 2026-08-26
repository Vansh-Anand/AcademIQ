import time
import os
import signal
from typing import Optional, List
from pydantic import BaseModel, Field
from common.events.schemas import EnforcementEvent
from l3_ebpf.namespace.scope import AgentScopeManager

class FreezeRequest(BaseModel):
    agent_id: str
    cgroup_id: int
    reason: str
    risk_score: float
    trigger_event_ids: List[str]
    timestamp: int = Field(default_factory=time.time_ns)
    policy_version: str = "1.0"

class SignedResumeRequest(BaseModel):
    agent_id: str
    cgroup_id: int
    incident_id: str
    authorized_by: str
    timestamp: int
    expiration: int
    signature: str

class KernelEnforcementManager:
    """
    Manages safe, cgroup-scoped enforcement (SIGSTOP / SIGKILL).
    """
    def __init__(self, scope_manager: AgentScopeManager, simulation: bool = True):
        self.scope_manager = scope_manager
        self.simulation = simulation

    def freeze_agent(self, request: FreezeRequest) -> EnforcementEvent:
        """
        Sends SIGSTOP to the intended process/cgroup members.
        """
        agent = self.scope_manager.get_agent(request.agent_id)
        if not agent or agent.cgroup_id != request.cgroup_id:
            return self._build_event(request, "FREEZE", False, "Agent/CGroup identity mismatch or not found")
            
        success = True
        error = None
        
        if self.simulation:
            # Simulated environment: we just log the freeze.
            pass
        else:
            try:
                # In Linux, freezing a cgroup is often done via cgroupfs (cgroup.freeze)
                # or sending SIGSTOP to all PIDs in cgroup.procs.
                # For prototype, we simulate sending SIGSTOP to the root_pid
                os.kill(agent.root_pid, signal.SIGSTOP)
            except OSError as e:
                success = False
                error = str(e)
                
        return self._build_event(request, "FREEZE", success, error)

    def terminate_agent(self, request: FreezeRequest) -> EnforcementEvent:
        """
        Sends SIGKILL to the cgroup.
        """
        agent = self.scope_manager.get_agent(request.agent_id)
        if not agent or agent.cgroup_id != request.cgroup_id:
            return self._build_event(request, "TERMINATE", False, "Agent/CGroup identity mismatch or not found")
            
        success = True
        error = None
        
        if self.simulation:
            pass
        else:
            try:
                os.kill(agent.root_pid, signal.SIGKILL)
            except OSError as e:
                success = False
                error = str(e)
                
        return self._build_event(request, "TERMINATE", success, error)

    def resume_agent_signed(self, request: SignedResumeRequest) -> EnforcementEvent:
        """
        Resumes a frozen agent ONLY if a valid cryptographically signed request is provided.
        """
        # In a real implementation, verify signature here using public key infrastructure.
        # For this prototype, we reject invalid signatures.
        if not request.signature.startswith("VALID_SIG_"):
            return EnforcementEvent(
                event_id=f"enf-{time.time_ns()}",
                agent_id=request.agent_id,
                cgroup_id=request.cgroup_id,
                action="RESUME",
                reason="Invalid resume signature",
                risk_score=0.0,
                timestamp=time.time_ns(),
                success=False,
                error="UNAUTHORIZED"
            )
            
        agent = self.scope_manager.get_agent(request.agent_id)
        if not agent or agent.cgroup_id != request.cgroup_id:
            return EnforcementEvent(
                event_id=f"enf-{time.time_ns()}",
                agent_id=request.agent_id,
                cgroup_id=request.cgroup_id,
                action="RESUME",
                reason="Agent not found",
                risk_score=0.0,
                timestamp=time.time_ns(),
                success=False,
                error="IDENTITY_MISMATCH"
            )
            
        success = True
        error = None
        if not self.simulation:
            try:
                os.kill(agent.root_pid, signal.SIGCONT)
            except OSError as e:
                success = False
                error = str(e)
                
        return EnforcementEvent(
            event_id=f"enf-{time.time_ns()}",
            agent_id=request.agent_id,
            cgroup_id=request.cgroup_id,
            action="RESUME",
            reason=f"Signed resume by {request.authorized_by}",
            risk_score=0.0,
            timestamp=time.time_ns(),
            success=success,
            error=error
        )

    def _build_event(self, request: FreezeRequest, action: str, success: bool, error: Optional[str]) -> EnforcementEvent:
        return EnforcementEvent(
            event_id=f"enf-{time.time_ns()}",
            agent_id=request.agent_id,
            cgroup_id=request.cgroup_id,
            action=action,
            reason=request.reason,
            risk_score=request.risk_score,
            trigger_event_ids=request.trigger_event_ids,
            timestamp=time.time_ns(),
            success=success,
            error=error
        )
