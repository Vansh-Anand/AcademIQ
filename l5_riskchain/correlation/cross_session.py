import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from common.events.schemas import DetectionState

@dataclass
class CrossSessionRegistryEntry:
    sessions: List[str] = field(default_factory=list)
    first_seen_ns: int = 0
    last_seen_ns: int = 0
    count: int = 0
    signature: str = ""

class CrossSessionReplayDetector:
    """
    Tracks and identifies multi-step attack patterns across independent sessions 
    based on structural fingerprints.
    """
    def __init__(self, 
                 window_seconds: int = 3600,
                 repeat_threshold: int = 2,
                 coordinated_threshold: int = 3,
                 risk_threshold: float = 0.5):
        self.window_seconds = window_seconds
        self.repeat_threshold = repeat_threshold
        self.coordinated_threshold = coordinated_threshold
        self.risk_threshold = risk_threshold
        
        self._registry: Dict[str, CrossSessionRegistryEntry] = {}

    def register_session_fingerprint(self, 
                                     session_id: str, 
                                     fingerprint: str, 
                                     signature: str,
                                     path_risk_score: float,
                                     bayesian_probability: float,
                                     current_time_ns: Optional[int] = None) -> Dict[str, Any]:
        """
        Registers a structural fingerprint observed in a session and returns the detection state.
        """
        if current_time_ns is None:
            current_time_ns = time.time_ns()
            
        is_high_risk = path_risk_score >= self.risk_threshold or bayesian_probability >= self.risk_threshold
            
        if fingerprint not in self._registry:
            self._registry[fingerprint] = CrossSessionRegistryEntry(
                sessions=[session_id],
                first_seen_ns=current_time_ns,
                last_seen_ns=current_time_ns,
                count=1,
                signature=signature
            )
            return self._build_result(fingerprint, session_id, DetectionState.NEW_PATTERN, is_high_risk)
            
        entry = self._registry[fingerprint]
        
        if session_id not in entry.sessions:
            entry.sessions.append(session_id)
            entry.count += 1
            
        entry.last_seen_ns = current_time_ns
        
        is_within_window = (entry.last_seen_ns - entry.first_seen_ns) <= (self.window_seconds * 1_000_000_000)
        
        state = DetectionState.REPEATED_PATTERN
        
        if is_within_window and entry.count >= self.coordinated_threshold:
            state = DetectionState.COORDINATED_PATTERN
            
        if not is_high_risk:
            state = DetectionState.LEGITIMATE_REPEAT
        elif state == DetectionState.REPEATED_PATTERN and is_high_risk:
            state = DetectionState.REPLAY_ALERT
            
        return self._build_result(fingerprint, session_id, state, is_high_risk)
        
    def _build_result(self, 
                      fingerprint: str, 
                      current_session: str, 
                      state: DetectionState, 
                      is_high_risk: bool) -> Dict[str, Any]:
                      
        entry = self._registry[fingerprint]
        matching_sessions = [s for s in entry.sessions if s != current_session]
        
        return {
            "fingerprint": fingerprint,
            "signature": entry.signature,
            "current_session_id": current_session,
            "matching_session_ids": matching_sessions,
            "detection_state": state.value,
            "repeat_count": entry.count,
            "is_high_risk": is_high_risk,
            "first_seen_ns": entry.first_seen_ns,
            "last_seen_ns": entry.last_seen_ns
        }

    def get_pattern_statistics(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        entry = self._registry.get(fingerprint)
        if not entry:
            return None
        return {
            "signature": entry.signature,
            "count": entry.count,
            "sessions": entry.sessions
        }
