import time
from typing import List, Optional, Any
from pydantic import BaseModel

class SecuritySession(BaseModel):
    session_id: str
    agent_id: str
    security_mode: str
    attestation_state: str
    events: List[Any]
    incidents: List[Any]
    final_state: str
    evidence_chain_id: Optional[str]
    session_start: float
    session_end: Optional[float]
    configuration_hash: str
    policy_versions: dict
    model_versions: dict

class SecuritySessionManager:
    """Manages full lifecycle of an end-to-end security session."""
    
    def __init__(self):
        self.current_session: Optional[SecuritySession] = None

    def start_session(self, agent_id: str, mode: str, config_hash: str, policies: dict, models: dict) -> SecuritySession:
        import uuid
        self.current_session = SecuritySession(
            session_id=str(uuid.uuid4()),
            agent_id=agent_id,
            security_mode=mode,
            attestation_state="PENDING",
            events=[],
            incidents=[],
            final_state="RUNNING",
            evidence_chain_id=None,
            session_start=time.time(),
            session_end=None,
            configuration_hash=config_hash,
            policy_versions=policies,
            model_versions=models
        )
        return self.current_session

    def record_event(self, event: Any):
        if self.current_session:
            self.current_session.events.append(event)
            
    def record_incident(self, incident: Any):
        if self.current_session:
            self.current_session.incidents.append(incident)
            
    def end_session(self, final_state: str, chain_id: str):
        if self.current_session:
            self.current_session.final_state = final_state
            self.current_session.evidence_chain_id = chain_id
            self.current_session.session_end = time.time()
            return self.current_session
            
    def export_session(self):
        if self.current_session:
            return self.current_session.model_dump()
        return None
