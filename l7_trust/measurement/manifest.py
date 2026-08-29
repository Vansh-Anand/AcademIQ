import hashlib
import json
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel

class SecurityArtifactManifest(BaseModel):
    version: str = "1.0"
    l1_policy_hash: str
    l2_policy_hash: str
    l3_bpf_hash: str
    l4_model_hash: str
    l5_governance_hash: str
    configuration_hash: str
    
    def deterministic_bytes(self) -> bytes:
        d = self.model_dump()
        return json.dumps(d, sort_keys=True, separators=(',', ':')).encode('utf-8')
        
class SecurityMeasurement(BaseModel):
    measurement_id: str
    tee_type: str
    measurement_digest: str
    manifest_hash: str
    timestamp: float
    is_software: bool

class MeasurementGenerator:
    """Generates measurements representing the trusted state of the security components."""
    
    @staticmethod
    def generate_manifest_hash(manifest: SecurityArtifactManifest) -> str:
        return hashlib.sha256(manifest.deterministic_bytes()).hexdigest()
        
    @staticmethod
    def create_software_measurement(manifest: SecurityArtifactManifest, tee_type: str = "SIMULATION") -> SecurityMeasurement:
        import uuid
        manifest_hash = MeasurementGenerator.generate_manifest_hash(manifest)
        # In software/simulation, the MR (Measurement Register) is just the hash of the manifest
        digest = hashlib.sha384(manifest_hash.encode('utf-8')).hexdigest()
        
        return SecurityMeasurement(
            measurement_id=str(uuid.uuid4()),
            tee_type=tee_type,
            measurement_digest=digest,
            manifest_hash=manifest_hash,
            timestamp=time.time(),
            is_software=(tee_type == "SIMULATION")
        )
