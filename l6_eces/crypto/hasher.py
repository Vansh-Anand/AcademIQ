import json
import hashlib
from typing import Any, Dict

# Attempt to load blake3 if available
try:
    import blake3
    HAS_BLAKE3 = True
except ImportError:
    HAS_BLAKE3 = False

class CanonicalSerializer:
    """
    Serializes dictionaries into deterministic, canonical UTF-8 JSON.
    - Keys are sorted.
    - No spaces after separators.
    - Strict handling of unicode.
    """
    @staticmethod
    def serialize(obj: Any) -> bytes:
        if isinstance(obj, BaseModel):
            obj = obj.model_dump()
        return json.dumps(
            obj,
            sort_keys=True,
            ensure_ascii=True,
            separators=(',', ':')
        ).encode('utf-8')

class HashProvider:
    """
    Provides BLAKE3 hashing if available, falling back to SHA-256 with explicit recording.
    """
    DOMAIN = b"ACADEMIQ-ECES-V1"

    def __init__(self, force_algorithm: str = None):
        if force_algorithm == "SHA-256":
            self.algorithm = "SHA-256"
        else:
            self.algorithm = "BLAKE3" if HAS_BLAKE3 else "SHA-256"

    def hash(self, data: bytes) -> str:
        # Include domain separation
        payload = self.DOMAIN + b"|" + data
        
        if self.algorithm == "BLAKE3":
            return blake3.blake3(payload).hexdigest()
        else:
            return hashlib.sha256(payload).hexdigest()

    def hash_event(self, event_dict: Dict[str, Any]) -> str:
        serialized = CanonicalSerializer.serialize(event_dict)
        return self.hash(serialized)
        
    def verify(self, data: bytes, digest: str) -> bool:
        return self.hash(data) == digest

from pydantic import BaseModel
