from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class CanonicalEvidencePayload(BaseModel):
    schema_version: str = "1.0"
    event_id: str
    event_type: str
    timestamp_ns: int
    agent_id: str
    session_id: str
    trace_id: str
    source_layer: str
    payload: Dict[str, Any]
    policy_version: str
    model_version: str
    configuration_hash: str
    simulation: bool = False
    parent_event_id: Optional[str] = None
    related_event_ids: List[str] = []
    telemetry_source: str = "SIMULATION"

class GenesisRecord(BaseModel):
    chain_id: str
    created_at: int
    algorithm: str
    schema_version: str = "1.0"
    system_identity: str
    configuration_hash: str
    policy_hash: str
    model_manifest_hash: str
    genesis_hash: str # self hash

class EvidenceRecord(BaseModel):
    chain_id: str
    sequence_number: int
    event_id: str
    timestamp_ns: int
    event_type: str
    agent_id: str
    session_id: str
    trace_id: str
    source_layer: str
    payload: Dict[str, Any]
    canonical_payload_hash: str
    previous_hash: str
    event_hash: str
    signature: Optional[str] = None
    signature_algorithm: Optional[str] = None
    signer_key_id: Optional[str] = None
    attestation_reference: Optional[str] = None
    policy_version: str
    model_version: str
    configuration_hash: str
    telemetry_source: str
    simulation: bool = False
    parent_event_id: Optional[str] = None
    related_event_ids: List[str] = []
    redaction_mode: str = "STANDARD"

class EvidenceManifest(BaseModel):
    package_id: str
    chain_id: str
    incident_ids: List[str]
    sequence_start: int
    sequence_end: int
    created_at: int
    exported_at: int
    hash_algorithm: str
    signature_algorithm: str
    signer_type: str
    signer_key_id: str
    redaction_mode: str
    policy_version: str
    model_versions: List[str]
    configuration_hash: str
    event_count: int
    package_hash: str
    verification_status: str

class ChainHead(BaseModel):
    chain_id: str
    latest_sequence: int
    latest_event_hash: str
    updated_at: int
    segment_id: str

class EvidenceCheckpoint(BaseModel):
    chain_id: str
    sequence_start: int
    sequence_end: int
    head_hash: str
    timestamp: int
    record_count: int
    signature: Optional[str] = None

class EvidenceHealthEvent(BaseModel):
    timestamp_ns: int
    queue_depth: int
    events_received: int
    events_persisted: int
    events_failed: int
    events_dropped: int
    status: str # HEALTHY, DEGRADED, FAILED
