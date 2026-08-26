import time
import uuid
import threading
from typing import Optional, List, Dict, Any

from common.events.base import BaseEvent
from l6_eces.chain.schemas import CanonicalEvidencePayload, EvidenceRecord, GenesisRecord
from l6_eces.chain.store import EvidenceStore, EvidenceRecoveryManager
from l6_eces.crypto.hasher import HashProvider, CanonicalSerializer
from l6_eces.crypto.signer import HardwareSigner

class EvidenceChainWriter:
    """Manages the causal chain creation and cryptographic linkage."""
    
    def __init__(self, 
                 store: EvidenceStore, 
                 hasher: HashProvider, 
                 signer: HardwareSigner,
                 system_identity: str = "AcademIQ-Prototype"):
        self.store = store
        self.hasher = hasher
        self.signer = signer
        self.system_identity = system_identity
        
        self.chain_id = f"chain-{uuid.uuid4()}"
        self.sequence_number = 0
        self.previous_hash = ""
        
        self._lock = threading.Lock()
        self._initialize_chain()
        
    def _initialize_chain(self):
        recovery = EvidenceRecoveryManager(self.store)
        head = recovery.recover()
        
        if head:
            # Continue from existing chain
            self.chain_id = head.chain_id
            self.sequence_number = head.latest_sequence
            self.previous_hash = head.latest_event_hash
        else:
            # Genesis
            genesis = GenesisRecord(
                chain_id=self.chain_id,
                created_at=time.time_ns(),
                algorithm=self.hasher.algorithm,
                system_identity=self.system_identity,
                configuration_hash="CONFIG_HASH_STUB",
                policy_hash="POLICY_HASH_STUB",
                model_manifest_hash="MODEL_HASH_STUB",
                genesis_hash=""
            )
            
            # Genesis hash is the hash of its own canonical payload sans genesis_hash
            canonical = CanonicalSerializer.serialize(genesis.model_dump(exclude={'genesis_hash'}))
            genesis.genesis_hash = self.hasher.hash(canonical)
            
            self.store.append_genesis(genesis)
            self.previous_hash = genesis.genesis_hash
            
    def append_event(self, event: BaseEvent, source_layer: str, redaction_mode: str = "STANDARD") -> EvidenceRecord:
        with self._lock:
            # 1. Increment Sequence
            self.sequence_number += 1
            
            # 2. Canonicalize
            # Normally we'd redact first. We assume redactor is called before or here.
            payload = CanonicalEvidencePayload(
                event_id=event.event_id if hasattr(event, 'event_id') else f"evt-{uuid.uuid4()}",
                event_type=getattr(event, 'event_type', type(event).__name__),
                timestamp_ns=getattr(event, 'timestamp_ns', time.time_ns()),
                agent_id=getattr(event, 'agent_id', "system"),
                session_id=getattr(event, 'session_id', "system"),
                trace_id=getattr(event, 'trace_id', "system"),
                source_layer=source_layer,
                payload=event.model_dump(),
                policy_version="1.0",
                model_version="1.0",
                configuration_hash="CONFIG_HASH",
                parent_event_id=getattr(event, 'parent_event_id', None)
            )
            
            canonical_bytes = CanonicalSerializer.serialize(payload.model_dump())
            payload_hash = self.hasher.hash(canonical_bytes)
            
            # 3. Hash Chain
            # H_n = Hash( payload_hash || previous_hash || sequence_number )
            # We use structured string concatenation as domain separated values
            chain_input = f"{payload_hash}|{self.previous_hash}|{self.sequence_number}".encode('utf-8')
            event_hash = self.hasher.hash(chain_input)
            
            # 4. Sign
            # We sign the event_hash.
            sig = self.signer.sign(event_hash.encode('utf-8'))
            
            record = EvidenceRecord(
                chain_id=self.chain_id,
                sequence_number=self.sequence_number,
                event_id=payload.event_id,
                timestamp_ns=payload.timestamp_ns,
                event_type=payload.event_type,
                agent_id=payload.agent_id,
                session_id=payload.session_id,
                trace_id=payload.trace_id,
                source_layer=source_layer,
                payload=payload.payload,
                canonical_payload_hash=payload_hash,
                previous_hash=self.previous_hash,
                event_hash=event_hash,
                signature=sig,
                signature_algorithm="ECDSA-P256" if hasattr(self.signer, "_sk") else "UNKNOWN",
                signer_key_id=self.signer.get_key_id(),
                policy_version=payload.policy_version,
                model_version=payload.model_version,
                configuration_hash=payload.configuration_hash,
                telemetry_source=payload.telemetry_source,
                parent_event_id=payload.parent_event_id,
                redaction_mode=redaction_mode
            )
            
            # 5. Persist
            self.store.append(record)
            
            # 6. Update Head
            self.previous_hash = event_hash
            
            return record
