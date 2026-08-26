import time
import uuid
from typing import Optional, Dict

from pydantic import BaseModel
from l3_ebpf.enforcement.kernel import KernelEnforcementManager, FreezeRequest, SignedResumeRequest
from common.events.schemas import EnforcementEvent, GovernanceDecision

class ThrottleRequest(BaseModel):
    agent_id: str
    cgroup_id: int
    cpu_limit: float # 0.0 to 1.0 (percent)
    memory_limit: int # bytes
    io_limit: int # bytes/sec
    network_limit: int # bytes/sec
    duration: int # ms
    reason: str

class L5EnforcementManager:
    """Coordinates execution of L5 Governance decisions via L3 Kernel enforcement."""
    
    def __init__(self, kernel_manager: KernelEnforcementManager):
        self.kernel_manager = kernel_manager
        # Track active states to avoid redundant freezes
        self._agent_states: Dict[str, str] = {}
        
    def execute_decision(self, decision: GovernanceDecision, agent_id: str, cgroup_id: int, incident_id: str, trigger_event_ids: list) -> Optional[EnforcementEvent]:
        current_state = self._agent_states.get(agent_id, "RUNNING")
        
        # Hysteresis/Idempotency check
        if decision.decision == "FREEZE" and current_state == "FROZEN":
            return None
        if decision.decision == "THROTTLE" and current_state == "THROTTLED":
            return None
            
        if decision.decision == "WARN":
            # Just generate an audit event, no kernel interaction required.
            event = EnforcementEvent(
                event_id=f"enf-{uuid.uuid4()}",
                incident_id=incident_id,
                agent_id=agent_id,
                cgroup_id=str(cgroup_id),
                action="WARN",
                reason=decision.explanation,
                risk_score=decision.risk_probability,
                trigger_event_ids=trigger_event_ids,
                timestamp_ns=time.time_ns(),
                success=True
            )
            self._agent_states[agent_id] = "WARNED"
            return event
            
        elif decision.decision == "THROTTLE":
            # In a real environment, we'd write to cgroupfs (cpu.max, memory.max).
            # We simulate this abstraction.
            req = ThrottleRequest(
                agent_id=agent_id,
                cgroup_id=cgroup_id,
                cpu_limit=0.1, # 10%
                memory_limit=1024 * 1024 * 100, # 100MB
                io_limit=1024 * 1024, # 1MB/s
                network_limit=1024 * 1024, # 1MB/s
                duration=60000,
                reason=decision.explanation
            )
            event = EnforcementEvent(
                event_id=f"enf-{uuid.uuid4()}",
                incident_id=incident_id,
                agent_id=agent_id,
                cgroup_id=str(cgroup_id),
                action="THROTTLE",
                reason=decision.explanation,
                risk_score=decision.risk_probability,
                trigger_event_ids=trigger_event_ids,
                timestamp_ns=time.time_ns(),
                success=True # Simulated success
            )
            self._agent_states[agent_id] = "THROTTLED"
            return event
            
        elif decision.decision == "FREEZE":
            req = FreezeRequest(
                agent_id=agent_id,
                cgroup_id=cgroup_id,
                reason=decision.explanation,
                risk_score=decision.risk_probability,
                trigger_event_ids=trigger_event_ids,
                policy_version=decision.policy_version
            )
            
            # The L3 manager EnforcementEvent schema differs slightly from the L5 one,
            # so we adapt it. We should ideally unify them, but let's adapt for the prototype.
            l3_event = self.kernel_manager.freeze_agent(req)
            event = EnforcementEvent(
                event_id=l3_event.event_id,
                incident_id=incident_id,
                agent_id=agent_id,
                cgroup_id=str(cgroup_id),
                action="FREEZE",
                reason=l3_event.reason,
                risk_score=l3_event.risk_score,
                trigger_event_ids=l3_event.trigger_event_ids,
                timestamp_ns=time.time_ns(),
                success=l3_event.success,
                error=l3_event.error
            )
            if l3_event.success:
                self._agent_states[agent_id] = "FROZEN"
            return event
            
        return None
        
    def resume_agent(self, agent_id: str, cgroup_id: int, incident_id: str, signature: str, authorized_by: str) -> EnforcementEvent:
        req = SignedResumeRequest(
            agent_id=agent_id,
            cgroup_id=cgroup_id,
            incident_id=incident_id,
            authorized_by=authorized_by,
            timestamp=time.time_ns(),
            expiration=time.time_ns() + 300_000_000_000,
            signature=signature
        )
        l3_event = self.kernel_manager.resume_agent_signed(req)
        
        event = EnforcementEvent(
            event_id=l3_event.event_id,
            incident_id=incident_id,
            agent_id=agent_id,
            cgroup_id=str(cgroup_id),
            action="RESUME",
            reason=l3_event.reason,
            risk_score=l3_event.risk_score,
            trigger_event_ids=l3_event.trigger_event_ids,
            timestamp_ns=time.time_ns(),
            success=l3_event.success,
            error=l3_event.error
        )
        if l3_event.success:
            self._agent_states[agent_id] = "RUNNING"
            
        return event
