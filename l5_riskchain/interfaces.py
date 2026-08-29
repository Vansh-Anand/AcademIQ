from abc import ABC, abstractmethod
from typing import List, Any, Dict, Optional
from common.schemas.security import SecurityDecision

class RiskChainGraph(ABC):
    @abstractmethod
    def add_node(self, event: Any):
        pass

class RiskScorer(ABC):
    @abstractmethod
    def score(self, event: Any) -> float:
        pass

class BayesianRiskModel(ABC):
    @abstractmethod
    def update_priors(self, evidence: dict):
        pass

class GovernanceEngine(ABC):
    @abstractmethod
    def evaluate(self, risk_score: float) -> SecurityDecision:
        pass

class EnforcementController(ABC):
    @abstractmethod
    def enforce(self, decision: SecurityDecision):
        pass

class ECESRecorder(ABC):
    @abstractmethod
    def record(self, event: Any):
        pass

class ECESVerifier(ABC):
    @abstractmethod
    def verify_chain(self) -> bool:
        pass

class RiskPathAnalyzer(ABC):
    @abstractmethod
    def analyze(self, graph: RiskChainGraph) -> Optional[Dict[str, Any]]:
        pass

class ForensicExporter(ABC):
    @abstractmethod
    def export(self) -> str:
        pass
