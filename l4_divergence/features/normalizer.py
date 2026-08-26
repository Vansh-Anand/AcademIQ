import json
import math
from typing import List, Dict, Optional

class FeatureNormalizer:
    """Z-score normalization for flat numeric features. Ensures training/test separation."""
    def __init__(self):
        self.means: List[float] = []
        self.stds: List[float] = []
        self.is_fit = False
        
    def fit(self, dataset_features: List[List[float]]) -> None:
        if not dataset_features:
            return
            
        num_features = len(dataset_features[0])
        self.means = [0.0] * num_features
        self.stds = [0.0] * num_features
        n = len(dataset_features)
        
        # Mean
        for row in dataset_features:
            for i, val in enumerate(row):
                self.means[i] += val
        self.means = [m / n for m in self.means]
        
        # Variance / Std
        variances = [0.0] * num_features
        for row in dataset_features:
            for i, val in enumerate(row):
                variances[i] += (val - self.means[i]) ** 2
        
        self.stds = [math.sqrt(v / n) for v in variances]
        
        # Avoid division by zero
        self.stds = [s if s > 1e-6 else 1.0 for s in self.stds]
        self.is_fit = True
        
    def transform(self, sample: List[float]) -> List[float]:
        if not self.is_fit:
            raise RuntimeError("Normalizer is not fit yet.")
        if len(sample) != len(self.means):
            raise ValueError(f"Feature dimension mismatch: expected {len(self.means)}, got {len(sample)}")
            
        return [(val - self.means[i]) / self.stds[i] for i, val in enumerate(sample)]
        
    def save(self, filepath: str) -> None:
        with open(filepath, 'w') as f:
            json.dump({
                "means": self.means,
                "stds": self.stds,
                "is_fit": self.is_fit,
                "version": "1.0"
            }, f)
            
    def load(self, filepath: str) -> None:
        with open(filepath, 'r') as f:
            data = json.load(f)
            self.means = data["means"]
            self.stds = data["stds"]
            self.is_fit = data["is_fit"]
