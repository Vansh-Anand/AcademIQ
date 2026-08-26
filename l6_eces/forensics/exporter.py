import os
import zipfile
import json
import uuid
import time
from typing import List, Dict, Any

from l6_eces.chain.store import EvidenceStore
from l6_eces.chain.schemas import EvidenceManifest
from l6_eces.crypto.hasher import HashProvider

class EvidenceExporter:
    """Exports evidence chains into forensic zip packages with manifests."""
    
    def __init__(self, store: EvidenceStore, hasher: HashProvider, signer):
        self.store = store
        self.hasher = hasher
        self.signer = signer
        
    def export_chain(self, export_dir: str = ".data/exports") -> str:
        os.makedirs(export_dir, exist_ok=True)
        records = self.store.read_all()
        
        if not records:
            raise ValueError("No records to export")
            
        genesis = records[0]["data"]
        chain_id = genesis.get("chain_id")
        
        package_id = f"pkg-{uuid.uuid4()}"
        zip_path = os.path.join(export_dir, f"{package_id}.zip")
        
        # Determine sequence range
        sequences = [r["data"].get("sequence_number") for r in records if r.get("_type") == "evidence"]
        seq_start = sequences[0] if sequences else 0
        seq_end = sequences[-1] if sequences else 0
        
        manifest = EvidenceManifest(
            package_id=package_id,
            chain_id=chain_id,
            incident_ids=[], # Can be populated if filtering by incident
            sequence_start=seq_start,
            sequence_end=seq_end,
            created_at=genesis.get("created_at"),
            exported_at=time.time_ns(),
            hash_algorithm=self.hasher.algorithm,
            signature_algorithm="ECDSA-P256",
            signer_type=self.signer.get_attestation()["signer_type"],
            signer_key_id=self.signer.get_key_id(),
            redaction_mode="STANDARD",
            policy_version=genesis.get("policy_hash", "1.0"),
            model_versions=[],
            configuration_hash=genesis.get("configuration_hash", ""),
            event_count=len(records),
            package_hash="",
            verification_status="UNVERIFIED"
        )
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add evidence jsonl directly
            zipf.write(self.store.chain_file, arcname="evidence.jsonl")
            
            # Create manifest JSON
            manifest_json = manifest.model_dump_json(indent=2)
            zipf.writestr("manifest.json", manifest_json)
            
        # Hash the zip file for external integrity
        with open(zip_path, 'rb') as f:
            zip_bytes = f.read()
            manifest.package_hash = self.hasher.hash(zip_bytes)
            
        # Re-write the manifest with the package_hash
        with zipfile.ZipFile(zip_path, 'a', zipfile.ZIP_DEFLATED) as zipf:
            manifest_json = manifest.model_dump_json(indent=2)
            zipf.writestr("manifest.json", manifest_json)
            
        return zip_path
