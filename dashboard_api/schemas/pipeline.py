from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from dashboard_api.schemas.common import ExecutionMode

class L1Outcome(BaseModel):
    decision: Optional[str] = None
    latency: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class L2Outcome(BaseModel):
    decision: Optional[str] = None
    normalized_command: Optional[str] = None
    detection_reason: Optional[str] = None
    latency: Optional[float] = None

class L3Outcome(BaseModel):
    status: str
    event_count: Optional[int] = None
    anomalies: Optional[int] = None
    execution_mode: ExecutionMode

class L4Outcome(BaseModel):
    isolation_forest_score: Optional[float] = None
    siamese_score: Optional[float] = None
    ensemble_score: Optional[float] = None
    drift_state: Optional[str] = None
    execution_mode: ExecutionMode

class L5Outcome(BaseModel):
    bayesian_probability: Optional[float] = None
    governance_state: Optional[str] = None
    highest_risk_path: Optional[str] = None
    cross_session_status: Optional[str] = None
    execution_mode: Optional[ExecutionMode] = None

class L6Outcome(BaseModel):
    evidence_chain_reference: Optional[str] = None
    chain_status: Optional[str] = None
    storage_backend: Optional[str] = None
    execution_mode: Optional[ExecutionMode] = None

class L7Outcome(BaseModel):
    isolation_status: Optional[str] = None
    scope_information: Optional[str] = None
    execution_mode: Optional[ExecutionMode] = None

class PipelineRunRequest(BaseModel):
    scenario_id: str = Field(..., description="The ID of the predefined safe scenario")

class PipelineRunResponse(BaseModel):
    session_id: str
    scenario_id: str
    overall_decision: str
    stopping_layer: str
    total_latency_ns: float
    L1: Optional[L1Outcome] = None
    L2: Optional[L2Outcome] = None
    L3: Optional[L3Outcome] = None
    L4: Optional[L4Outcome] = None
    L5: Optional[L5Outcome] = None
    L6: Optional[L6Outcome] = None
    L7: Optional[L7Outcome] = None
