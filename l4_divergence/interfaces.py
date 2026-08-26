from abc import ABC, abstractmethod
from typing import List, Dict, Any
from common.events.schemas import DivergenceEvent

class TrajectoryWindow(ABC):
    @abstractmethod
    def add_event(self, event: Any):
        pass

    @abstractmethod
    def get_window(self) -> List[Any]:
        pass

class FeatureExtractor(ABC):
    @abstractmethod
    def extract(self, window: List[Any]) -> List[float]:
        pass

class SiameseEncoder(ABC):
    @abstractmethod
    def encode(self, features: List[float]) -> List[float]:
        pass

class IsolationForestDetector(ABC):
    @abstractmethod
    def predict_anomaly(self, encoded_features: List[float]) -> float:
        pass

class DivergenceEnsemble(ABC):
    @abstractmethod
    def calculate_divergence(self, features: List[float]) -> DivergenceEvent:
        pass

class ECEManager(ABC):
    @abstractmethod
    def check_envelope(self, event: Any) -> bool:
        pass

class HardwareFeatureFusion(ABC):
    @abstractmethod
    def fuse(self, software_features: List[float], hardware_features: List[float]) -> List[float]:
        pass
