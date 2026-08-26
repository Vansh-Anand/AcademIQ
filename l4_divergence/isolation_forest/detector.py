import pickle
import numpy as np
from sklearn.ensemble import IsolationForest
from typing import List

class IsolationForestDetector:
    """Wrapper around scikit-learn's Isolation Forest for behavioral anomalies."""
    def __init__(self, n_estimators: int = 100, contamination: float = 'auto', random_state: int = 42):
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1
        )
        self.is_fit = False
        
    def fit(self, X: np.ndarray) -> None:
        """Fit on legitimate baseline data."""
        self.model.fit(X)
        self.is_fit = True
        
    def score(self, X: np.ndarray) -> np.ndarray:
        """
        Returns anomaly scores mapped to [0, 1] conceptually.
        scikit-learn decision_function returns negative values for anomalies, positive for normal.
        We invert it so higher = more anomalous.
        """
        if not self.is_fit:
            raise RuntimeError("IsolationForestDetector not fitted.")
            
        scores = self.model.decision_function(X) # Higher means more NORMAL
        # Invert so higher means more ANOMALOUS, and shift roughly to [0, 1] range.
        # This will be properly calibrated by ScoreCalibrator later.
        anom_scores = 0.5 - (scores / 2.0)
        return np.clip(anom_scores, 0.0, 1.0)
        
    def save(self, filepath: str) -> None:
        with open(filepath, 'wb') as f:
            pickle.dump({
                "model": self.model,
                "is_fit": self.is_fit
            }, f)
            
    def load(self, filepath: str) -> None:
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.model = data["model"]
            self.is_fit = data["is_fit"]
