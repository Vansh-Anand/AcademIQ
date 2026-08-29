import time
from typing import Dict, List, Optional, Tuple
from common.events.schemas import SyscallEvent, BaseEvent
from l2_sdn.events import NormalizedCommandEvent
from pydantic import Field

import uuid

class UnexpectedExecutionEvent(BaseEvent):
    event_type: str = "UnexpectedExecution"
    event_id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4()}")
    timestamp_ns: int = Field(default_factory=time.time_ns)
    layer: str = "L3"
    trace_id: str = "unknown"
    agent_id: str
    syscall_event: SyscallEvent
    reason: str

class ExecutionCorrelationManager:
    """
    Correlates L2 authorized actions (NormalizedCommandEvent) with L3 actual kernel execution (SyscallEvent).
    Detects unexpected execution or network activity.
    """
    def __init__(self, time_window_ns: int = 5_000_000_000): # 5 seconds
        self.time_window_ns = time_window_ns
        self._pending_l2_decisions: Dict[str, List[NormalizedCommandEvent]] = {}
        
    def register_l2_decision(self, event: NormalizedCommandEvent):
        """Called when L2 ALLOWS a command."""
        if event.policy_result != "ALLOW":
            return
            
        agent_id = event.agent_id
        if agent_id not in self._pending_l2_decisions:
            self._pending_l2_decisions[agent_id] = []
            
        self._pending_l2_decisions[agent_id].append(event)
        
    def correlate_syscall(self, event: SyscallEvent) -> Tuple[bool, Optional[UnexpectedExecutionEvent]]:
        """
        Called when L3 observes an execve or connect. 
        Returns (correlated: bool, anomaly_event: Optional).
        """
        self._expire_pending_actions()
        
        agent_id = event.agent_id
        
        # If we see an execve
        if event.syscall_name in ("execve", "execveat"):
            executable = event.executable
            if not executable:
                return False, UnexpectedExecutionEvent(agent_id=agent_id, syscall_event=event, reason="Missing executable in execve")
                
            # Basic correlation logic: does this executable match any pending L2 approved commands?
            # A real implementation would match canonical AST paths with exact process trees.
            matched = False
            pending = self._pending_l2_decisions.get(agent_id, [])
            for p in pending:
                # Naive matching: check if the executable name is within the transformations or original.
                # In Phase 3, we didn't store the exact canonical executable in NormalizedCommandEvent directly,
                # but we know it's allowed.
                # For demonstration, we assume it's correlated if there's any pending L2 event in the window.
                # A robust system extracts the executable from the canonical hash dictionary (which we would persist).
                matched = True
                break
                
            if not matched:
                return False, UnexpectedExecutionEvent(agent_id=agent_id, syscall_event=event, reason=f"Unexpected execve({executable}) without L2 authorization")
                
            return True, None
            
        # If we see network connect
        if event.syscall_name == "connect":
            # For this Phase, L2 shell policy blocked network usage (`network_policy.allow_curl = false`)
            # Any connect syscall is considered unauthorized if not explicitly whitelisted.
            return False, UnexpectedExecutionEvent(agent_id=agent_id, syscall_event=event, reason=f"Unauthorized network activity to {event.destination_ip}:{event.destination_port}")
            
        # If we see ptrace
        if event.syscall_name == "ptrace":
            # Ptrace from a monitored agent is heavily scrutinized as potential privilege escalation/process injection
            return False, UnexpectedExecutionEvent(agent_id=agent_id, syscall_event=event, reason="Unauthorized process manipulation (ptrace attempt detected)")
            
        return True, None
        
    def _expire_pending_actions(self):
        now = time.time_ns()
        for agent_id, events in list(self._pending_l2_decisions.items()):
            valid_events = [e for e in events if (now - e.timestamp_ns) <= self.time_window_ns]
            if not valid_events:
                del self._pending_l2_decisions[agent_id]
            else:
                self._pending_l2_decisions[agent_id] = valid_events
