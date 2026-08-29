import time
from typing import Dict, Optional, List
from pydantic import BaseModel

class SecurityDegradationEvent(BaseModel):
    event_id: str
    component: str
    old_state: str
    new_state: str
    reason: str
    timestamp: float
    security_mode: str
    affected_controls: List[str]
    recommended_action: str

class SecurityHealthState(BaseModel):
    L1: str = "HEALTHY"
    L2: str = "HEALTHY"
    L3: str = "HEALTHY"
    L4: str = "HEALTHY"
    L5: str = "HEALTHY"
    ECES: str = "HEALTHY"
    TPM: str = "UNAVAILABLE"
    TEE: str = "UNAVAILABLE"

class SecurityHealthManager:
    """Manages the global security health and fail-safe transitions."""
    
    def __init__(self, mode: str = "STANDARD"):
        self.state = SecurityHealthState()
        self.mode = mode
        self.degradations: List[SecurityDegradationEvent] = []

    def update_component(self, component: str, new_status: str, reason: str = "") -> Optional[SecurityDegradationEvent]:
        old_status = getattr(self.state, component, "UNKNOWN")
        if old_status == new_status:
            return None
            
        setattr(self.state, component, new_status)
        
        import uuid
        event = SecurityDegradationEvent(
            event_id=str(uuid.uuid4()),
            component=component,
            old_state=old_status,
            new_state=new_status,
            reason=reason,
            timestamp=time.time(),
            security_mode=self.mode,
            affected_controls=[component],
            recommended_action="Restart component" if new_status == "FAILED" else "Monitor"
        )
        self.degradations.append(event)
        
        # If in HIGH_ASSURANCE, certain failures must HALT
        if self.mode == "HIGH_ASSURANCE" and new_status == "FAILED":
            if component in ["ECES", "L3", "TEE", "TPM"]:
                raise RuntimeError(f"HIGH_ASSURANCE mode halting due to critical failure in {component}: {reason}")
                
        return event

    def get_overall_state(self) -> str:
        statuses = [
            self.state.L1, self.state.L2, self.state.L3, 
            self.state.L4, self.state.L5, self.state.ECES
        ]
        if "FAILED" in statuses:
            return "FAILED"
        if "DEGRADED" in statuses:
            return "DEGRADED"
        return "HEALTHY"
