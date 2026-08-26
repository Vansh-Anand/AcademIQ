from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class BaseEvent(BaseModel):
    event_id: str = Field(..., description="Unique identifier for the event")
    schema_version: str = Field(default="1.0", description="Schema version")
    timestamp_ns: int = Field(..., description="Timestamp in nanoseconds")
    agent_id: str = Field(default="default-agent", description="ID of the agent")
    session_id: str = Field(default="default-session", description="ID of the session")
    task_id: str = Field(default="default-task", description="ID of the task")
    layer: str = Field(..., description="AcademIQ layer that generated the event (e.g., L1, L2, L3)")
    event_type: str = Field(..., description="Type of the event")
    parent_event_id: Optional[str] = Field(default=None, description="Parent event ID for correlation")
    trace_id: str = Field(..., description="Distributed trace ID")
    simulation: bool = Field(default=False, description="Whether this event was generated in simulation mode")
    integrity_metadata: Dict[str, Any] = Field(default_factory=dict, description="Hashes or signatures")
