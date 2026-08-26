from pydantic import Field
from typing import List, Optional, Dict, Any
from .base import BaseEvent

class ToolInvocationEvent(BaseEvent):
    event_type: str = Field(default="ToolInvocation")
    tool_name: str
    arguments: Dict[str, Any]

class ShellCommandEvent(BaseEvent):
    event_type: str = Field(default="ShellCommand")
    raw_command: str

class NormalizedCommandEvent(BaseEvent):
    event_type: str = Field(default="NormalizedCommand")
    normalized_command: str
    passes_applied: int

class PathResolutionEvent(BaseEvent):
    event_type: str = Field(default="PathResolution")
    requested_path: str
    resolved_path: str
    inode_id: Optional[int] = None
    device_id: Optional[int] = None

class SyscallEvent(BaseEvent):
    event_type: str = Field(default="Syscall")
    syscall_name: str
    arguments: List[Any]
    pid: int
    return_code: Optional[int] = None

class HardwarePerformanceEvent(BaseEvent):
    event_type: str = Field(default="HardwarePerformance")
    cycles: Optional[int] = None
    instructions: Optional[int] = None
    ipc: Optional[float] = None
    cache_references: Optional[int] = None
    cache_misses: Optional[int] = None
    branch_instructions: Optional[int] = None
    branch_misses: Optional[int] = None

class DivergenceEvent(BaseEvent):
    event_type: str = Field(default="Divergence")
    divergence_score: float
    features_analyzed: int

class TEEAttestationEvent(BaseEvent):
    event_type: str = Field(default="TEEAttestation")
    provider_name: str
    quote_data: str
    verified: bool
