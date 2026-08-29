from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from common.events.schemas import ToolInvocationEvent, ShellCommandEvent, RiskNode
from common.schemas.security import DecisionEnum

class LayerOutcome(BaseModel):
    decision: str = "NOT_EXECUTED" # e.g. ALLOW, BLOCK, WARN, NOT_EXECUTED
    risk_score: Optional[float] = None
    confidence: Optional[float] = None
    reason_codes: List[str] = Field(default_factory=list)
    latency_ns: Optional[int] = None

class LayerOutcomes(BaseModel):
    L1: LayerOutcome = Field(default_factory=LayerOutcome)
    L2: LayerOutcome = Field(default_factory=LayerOutcome)
    L3: LayerOutcome = Field(default_factory=LayerOutcome)
    L4: LayerOutcome = Field(default_factory=LayerOutcome)
    L5: LayerOutcome = Field(default_factory=LayerOutcome)

class ExperimentResult(BaseModel):
    scenario_id: str
    start_timestamp_ns: int
    end_timestamp_ns: int
    total_latency_ns: int
    attack_blocked: bool
    attack_success: bool
    stopping_layer: Optional[str] = None
    layer_outcomes: LayerOutcomes = Field(default_factory=LayerOutcomes)
    l3_events_processed: int = 0
    l3_anomalies_detected: int = 0
    errors: List[str] = Field(default_factory=list)
    evidence_reference: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ScenarioDefinition(BaseModel):
    scenario_id: str
    scenario_name: str
    description: str
    category: str
    session_id: Optional[str] = None
    timestamp_ns: Optional[int] = None
    agent_events: List[ToolInvocationEvent] = Field(default_factory=list)
    shell_events: List[ShellCommandEvent] = Field(default_factory=list)
    risk_nodes: List[RiskNode] = Field(default_factory=list)
    risk_edges: List[Any] = Field(default_factory=list)
    telemetry_trace: Optional[str] = None # Path to JSONL file
    expected_security_outcome: DecisionEnum
    metadata: Dict[str, Any] = Field(default_factory=dict)
