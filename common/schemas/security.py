from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class DecisionEnum(str, Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    THROTTLE = "THROTTLE"
    BLOCK = "BLOCK"
    FREEZE = "FREEZE"

class SecurityDecision(BaseModel):
    decision: DecisionEnum
    reason_codes: List[str] = Field(default_factory=list)
    risk_score: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=1.0)
    source_layers: List[str] = Field(default_factory=list)
    related_event_ids: List[str] = Field(default_factory=list)
    timestamp_ns: int
    policy_version: str = Field(default="1.0")
    model_version: str = Field(default="1.0")
