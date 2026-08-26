import json
import time
from typing import Dict, List, Optional
from common.events.schemas import SecurityIncident

class IncidentStore:
    """Append-oriented Security Incident store."""
    
    def __init__(self):
        # We store incidents in memory. 
        # In production this would be a DB or append-only log.
        self._incidents: Dict[str, SecurityIncident] = {}
        
    def create(self, incident: SecurityIncident) -> bool:
        if incident.incident_id in self._incidents:
            return False
        self._incidents[incident.incident_id] = incident
        return True
        
    def update_status(self, incident_id: str, new_status: str, explanation: str = "") -> bool:
        """Transitions an incident state (e.g. OPEN -> CONTAINED)."""
        valid_statuses = ["OPEN", "ACKNOWLEDGED", "CONTAINED", "RESOLVED", "FALSE_POSITIVE"]
        if new_status not in valid_statuses:
            return False
            
        incident = self._incidents.get(incident_id)
        if not incident:
            return False
            
        # We don't overwrite the original object in an append-only model,
        # we would write a new log. Here we simulate it by updating the model's status.
        incident.status = new_status
        incident.updated_at = time.time_ns()
        if explanation:
            incident.explanation = f"{incident.explanation} | Status update: {explanation}"
            
        self._incidents[incident_id] = incident
        return True
        
    def get(self, incident_id: str) -> Optional[SecurityIncident]:
        return self._incidents.get(incident_id)
        
    def list_active(self) -> List[SecurityIncident]:
        return [i for i in self._incidents.values() if i.status in ["OPEN", "ACKNOWLEDGED", "CONTAINED"]]
