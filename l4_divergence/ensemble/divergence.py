from typing import Dict, Any

class ScoreCalibrator:
    """Calibrates raw scores into a normalized [0, 1] divergence scale."""
    def __init__(self):
        self.siam_min = 0.0
        self.siam_max = 1.0
        self.iso_min = 0.0
        self.iso_max = 1.0
        self.is_fit = False
        
    def fit(self, siam_scores: list, iso_scores: list):
        if not siam_scores or not iso_scores:
            return
            
        self.siam_min = min(siam_scores)
        self.siam_max = max(siam_scores)
        self.iso_min = min(iso_scores)
        self.iso_max = max(iso_scores)
        
        # Avoid zero division
        if self.siam_max - self.siam_min < 1e-6:
            self.siam_max += 0.1
        if self.iso_max - self.iso_min < 1e-6:
            self.iso_max += 0.1
            
        self.is_fit = True
        
    def calibrate_siamese(self, score: float) -> float:
        return max(0.0, min(1.0, (score - self.siam_min) / (self.siam_max - self.siam_min)))
        
    def calibrate_isolation(self, score: float) -> float:
        return max(0.0, min(1.0, (score - self.iso_min) / (self.iso_max - self.iso_min)))

class DivergenceEnsemble:
    """Soft-voting ensemble of Siamese and Isolation Forest models."""
    def __init__(self, siamese_weight: float = 0.5, isolation_weight: float = 0.5):
        self.siamese_weight = siamese_weight
        self.isolation_weight = isolation_weight
        self.calibrator = ScoreCalibrator()
        
    def evaluate(self, raw_siamese: float, raw_isolation: float) -> Dict[str, Any]:
        """Returns the blended and calibrated divergence score."""
        
        # We assume the calibrator provides safe fallbacks if not fit (e.g. returns raw bounded).
        if self.calibrator.is_fit:
            cal_siam = self.calibrator.calibrate_siamese(raw_siamese)
            cal_iso = self.calibrator.calibrate_isolation(raw_isolation)
        else:
            cal_siam = min(1.0, max(0.0, raw_siamese))
            cal_iso = min(1.0, max(0.0, raw_isolation))
            
        final_score = (cal_siam * self.siamese_weight) + (cal_iso * self.isolation_weight)
        
        return {
            "score": final_score,
            "siamese_component": cal_siam,
            "isolation_component": cal_iso,
            "raw_siamese": raw_siamese,
            "raw_isolation": raw_isolation
        }
