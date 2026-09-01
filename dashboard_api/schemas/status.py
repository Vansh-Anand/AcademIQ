from pydantic import BaseModel
from typing import List, Optional
from dashboard_api.schemas.pipeline import ExecutionMode

class LayerSystemStatus(BaseModel):
    layer_id: str
    name: str
    operational_status: str # OPERATIONAL, PARTIAL, SIMULATED, UNAVAILABLE, ERROR
    execution_mode: ExecutionMode
    description: str
    capabilities: List[str]
    limitations: List[str]

class CapabilityStatus(BaseModel):
    name: str
    status: str
    validation_level: str
    execution_mode: ExecutionMode

class InfrastructureStatus(BaseModel):
    name: str
    status: str
    execution_mode: ExecutionMode
    description: str

class SystemStatusResponse(BaseModel):
    api_version: str
    backend_status: str
    database_status: str
    overall_status: str
    overall_description: str
    infrastructure: List[InfrastructureStatus]
    layers: List[LayerSystemStatus]
    capabilities: List[CapabilityStatus]
