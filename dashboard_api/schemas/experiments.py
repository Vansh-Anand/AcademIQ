from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from .pipeline import ExecutionMode

class ExperimentNormalized(BaseModel):
    experiment_id: str
    title: str
    category: str
    description: str
    execution_mode: ExecutionMode
    model_name: Optional[str] = None
    sample_size: Optional[int] = None
    
    baseline_metrics: Optional[Dict[str, Any]] = None
    protected_metrics: Optional[Dict[str, Any]] = None
    
    detection_rate: Optional[float] = None
    attack_success_rate: Optional[float] = None
    false_positive_rate: Optional[float] = None
    
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    
    latency_metrics: Optional[Dict[str, Any]] = None
    key_findings: Optional[str] = None
    known_limitations: Optional[List[str]] = None
    
    raw_artifact: Optional[Dict[str, Any]] = None

class ExperimentSummary(BaseModel):
    experiment_id: str
    title: str
    category: str
    description: str
    execution_mode: ExecutionMode
    model_name: Optional[str] = None
    primary_metric: Optional[Dict[str, Any]] = None

class ExperimentListResponse(BaseModel):
    experiments: List[ExperimentSummary]
