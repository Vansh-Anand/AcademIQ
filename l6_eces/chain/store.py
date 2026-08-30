import json
import os
import threading
from typing import Optional, List, Dict, Any
from l6_eces.chain.schemas import EvidenceRecord, GenesisRecord, ChainHead

from abc import ABC, abstractmethod

class EvidenceStore(ABC):
    """Abstract Base Class for append-only evidence stores."""
    
    @abstractmethod
    def append_genesis(self, record: GenesisRecord):
        pass

    @abstractmethod
    def append(self, record: EvidenceRecord):
        pass

    @abstractmethod
    def read_all(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_chain_head(self) -> Optional[ChainHead]:
        pass

class JsonlEvidenceStore(EvidenceStore):
    """Append-only evidence store using JSON Lines for simple integrity."""
    def __init__(self, directory: str = ".data/evidence"):
        self.directory = directory
        os.makedirs(self.directory, exist_ok=True)
        self.chain_file = os.path.join(self.directory, "evidence.jsonl")
        self._lock = threading.Lock()
        
    def append_genesis(self, record: GenesisRecord):
        with self._lock:
            if os.path.exists(self.chain_file) and os.path.getsize(self.chain_file) > 0:
                raise RuntimeError("Cannot append genesis to non-empty chain")
            
            with open(self.chain_file, "a", encoding="utf-8") as f:
                f.write("G|" + record.model_dump_json() + "\n")
                f.flush()
                os.fsync(f.fileno())

    def append(self, record: EvidenceRecord):
        with self._lock:
            with open(self.chain_file, "a", encoding="utf-8") as f:
                f.write("E|" + record.model_dump_json() + "\n")
                f.flush()
                os.fsync(f.fileno())

    def read_all(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.chain_file):
            return []
            
        records = []
        with open(self.chain_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                type_flag, json_data = line.split("|", 1)
                records.append({
                    "_type": "genesis" if type_flag == "G" else "evidence",
                    "data": json.loads(json_data)
                })
        return records
        
    def get_chain_head(self) -> Optional[ChainHead]:
        if not os.path.exists(self.chain_file):
            return None
            
        last_evidence = None
        with open(self.chain_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("E|"):
                    last_evidence = json.loads(line.split("|", 1)[1])
                elif line.startswith("G|"):
                    genesis = json.loads(line.split("|", 1)[1])
                    if last_evidence is None:
                        # If only genesis exists, mock a head for it
                        return ChainHead(
                            chain_id=genesis["chain_id"],
                            latest_sequence=0,
                            latest_event_hash=genesis["genesis_hash"],
                            updated_at=genesis["created_at"],
                            segment_id="1"
                        )
                        
        if last_evidence:
            return ChainHead(
                chain_id=last_evidence["chain_id"],
                latest_sequence=last_evidence["sequence_number"],
                latest_event_hash=last_evidence["event_hash"],
                updated_at=last_evidence["timestamp_ns"],
                segment_id="1"
            )
            
        return None

class EvidenceRecoveryManager:
    """Recovers the chain in case of a crash or incomplete write."""
    def __init__(self, store: EvidenceStore):
        self.store = store
        
    def recover(self) -> Optional[ChainHead]:
        # A true recovery manager would scan sequentially, verify hashes,
        # and truncate at the first invalid hash. 
        # For prototype, we assume underlying store is consistent up to head.
        return self.store.get_chain_head()
