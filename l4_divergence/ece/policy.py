from common.events.schemas import WindowQuality

class BaselineAdmissionPolicy:
    """Anti-poisoning policy for admitting new samples into the ECE baseline."""
    
    def __init__(self, current_threshold: float, margin: float = 0.2):
        self.current_threshold = current_threshold
        self.margin = margin
        
    def is_admissible(self, score: float, quality: WindowQuality) -> bool:
        # Reject highly anomalous scores that might be an attack
        if score > self.current_threshold + self.margin:
            return False
            
        # Reject windows that are incomplete or drop events
        if quality.quality_score < 0.9 or quality.dropped_events > 0:
            return False
            
        return True
