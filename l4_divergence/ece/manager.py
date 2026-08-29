import numpy as np
import json
from typing import List, Dict, Optional
from l4_divergence.ece.cusum import CUSUMDriftDetector, DriftState

class ECEManager:
    """Manages the Emergent Capability Envelope threshold."""
    def __init__(self, percentile: float = 99.0, mode: str = "DYNAMIC"):
        self.percentile = percentile
        self.mode = mode # "DYNAMIC" or "STATIC"
        
        self.baseline_scores: List[float] = []
        self.threshold = 1.0 # High default until initialized
        self.version = "1.0"
        
        self.drift_detector: Optional[CUSUMDriftDetector] = None
        
    def enable_drift_detection(self, reference_value: float = 0.05, decision_threshold: float = 1.5, min_admitted_samples: int = 50):
        self.drift_detector = CUSUMDriftDetector(reference_value, decision_threshold, min_admitted_samples)
        
    def initialize(self, initial_legitimate_scores: List[float]) -> None:
        self.baseline_scores = initial_legitimate_scores
        self.recalibrate()
        
    def recalibrate(self) -> None:
        if not self.baseline_scores:
            self.threshold = 1.0
            return
            
        if self.mode == "DYNAMIC":
            self.threshold = float(np.percentile(self.baseline_scores, self.percentile))
        else:
            self.threshold = 0.5 # Static default
            
    def get_baseline_mean(self) -> float:
        if not self.baseline_scores:
            return 0.0
        return float(np.mean(self.baseline_scores))

    def process_observation(self, new_score: float, is_admitted: bool) -> bool:
        """
        Integrates CUSUM logic with the admission check.
        Returns True if a recalibration was just successfully completed.
        """
        # If drift detection is disabled, just append if admitted
        if not self.drift_detector:
            if is_admitted:
                self.update(new_score)
            return False
            
        if not is_admitted:
            self.drift_detector.rejected_candidates += 1
            return False
            
        # At this point, the observation is admitted by security gates.
        state = self.drift_detector.state
        
        if state in (DriftState.STABLE, DriftState.OBSERVING):
            self.drift_detector.observe(new_score, self.get_baseline_mean())
            self.update(new_score)
            return False
            
        # If in drift suspected or recalibration pending state
        if state in (DriftState.DRIFT_SUSPECTED, DriftState.RECALIBRATION_PENDING):
            ready = self.drift_detector.add_candidate(new_score)
            if ready:
                # Perform safe recalibration
                self.baseline_scores.extend(self.drift_detector.candidate_buffer)
                # Keep window size bounded in memory
                if len(self.baseline_scores) > 10000:
                    self.baseline_scores = self.baseline_scores[-10000:]
                
                self.recalibrate()
                self.drift_detector.state = DriftState.RECALIBRATED
                self.drift_detector.recalibration_count += 1
                self.drift_detector.reset()
                return True
                
        return False
            
    def update(self, new_score: float) -> None:
        # Appends a score if authorized by BaselineAdmissionPolicy
        self.baseline_scores.append(new_score)
        # Keep window size bounded in memory
        if len(self.baseline_scores) > 10000:
            self.baseline_scores = self.baseline_scores[-10000:]
            
    def save(self, filepath: str) -> None:
        with open(filepath, 'w') as f:
            json.dump({
                "threshold": self.threshold,
                "percentile": self.percentile,
                "mode": self.mode,
                "version": self.version,
                "num_samples": len(self.baseline_scores)
            }, f)
            
    def load(self, filepath: str) -> None:
        with open(filepath, 'r') as f:
            data = json.load(f)
            self.threshold = data["threshold"]
            self.percentile = data["percentile"]
            self.mode = data["mode"]
            self.version = data["version"]
            # Note: For privacy/space, we don't dump all historical scores, just the threshold.
            # Real recalibration requires retaining samples or passing them in.
