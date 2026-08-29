import time
from enum import Enum
from typing import List, Optional

class DriftState(Enum):
    STABLE = "STABLE"
    OBSERVING = "OBSERVING"
    DRIFT_SUSPECTED = "DRIFT_SUSPECTED"
    RECALIBRATION_PENDING = "RECALIBRATION_PENDING"
    RECALIBRATED = "RECALIBRATED"

class CUSUMDriftDetector:
    """Security-gated adaptive behavioral baseline recalibration using sustained drift evidence."""
    def __init__(self, reference_value: float = 0.05, decision_threshold: float = 1.5, min_admitted_samples: int = 50):
        self.k = reference_value
        self.h = decision_threshold
        self.min_admitted_samples = min_admitted_samples
        
        self.s_plus = 0.0
        self.s_minus = 0.0
        self.state = DriftState.STABLE
        
        self.candidate_buffer: List[float] = []
        
        # Metrics
        self.total_observations = 0
        self.drift_detections = 0
        self.recalibration_count = 0
        self.rejected_candidates = 0
        self.admitted_samples = 0
        self.observations_until_detection = 0

    def observe(self, x_t: float, baseline_mean: float) -> DriftState:
        """Process an observation that has already passed security admission gates."""
        self.total_observations += 1
        
        # Calculate CUSUM
        self.s_plus = max(0.0, self.s_plus + (x_t - baseline_mean - self.k))
        self.s_minus = max(0.0, self.s_minus + (baseline_mean - x_t - self.k))
        
        if self.state in (DriftState.STABLE, DriftState.OBSERVING):
            if self.s_plus > 0 or self.s_minus > 0:
                self.state = DriftState.OBSERVING
                
            if self.s_plus > self.h or self.s_minus > self.h:
                self.state = DriftState.DRIFT_SUSPECTED
                self.drift_detections += 1
                self.observations_until_detection = self.total_observations
                
        return self.state
        
    def add_candidate(self, x_t: float) -> bool:
        """Adds a candidate observation for recalibration. Returns True if ready to recalibrate."""
        if self.state in (DriftState.DRIFT_SUSPECTED, DriftState.RECALIBRATION_PENDING):
            self.state = DriftState.RECALIBRATION_PENDING
            self.candidate_buffer.append(x_t)
            self.admitted_samples += 1
            return len(self.candidate_buffer) >= self.min_admitted_samples
        return False
        
    def reset(self):
        """Resets the state after successful recalibration."""
        self.s_plus = 0.0
        self.s_minus = 0.0
        self.state = DriftState.STABLE
        self.candidate_buffer = []
        self.total_observations = 0
