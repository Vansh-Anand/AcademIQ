from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Any
import os
import uuid

# We attempt to use ecdsa for software signing. 
try:
    from ecdsa import SigningKey, SECP256k1
    HAS_ECDSA = True
except ImportError:
    HAS_ECDSA = False

class HardwareSigner(ABC):
    """Base interface for hardware and software signers."""
    
    @abstractmethod
    def generate_key(self) -> str:
        pass
        
    @abstractmethod
    def get_public_key(self) -> str:
        pass
        
    @abstractmethod
    def sign(self, data: bytes) -> str:
        pass
        
    @abstractmethod
    def verify(self, data: bytes, signature: str) -> bool:
        pass
        
    @abstractmethod
    def get_key_id(self) -> str:
        pass
        
    @abstractmethod
    def get_attestation(self) -> Dict[str, Any]:
        pass

class SoftwareSigner(HardwareSigner):
    """Development software signer using ECDSA P-256."""
    
    def __init__(self):
        self._key_id = f"soft-{uuid.uuid4()}"
        self._sk = None
        self._vk = None
        
    def generate_key(self) -> str:
        if not HAS_ECDSA:
            raise RuntimeError("ecdsa package not installed")
        self._sk = SigningKey.generate(curve=SECP256k1)
        self._vk = self._sk.get_verifying_key()
        return self._key_id
        
    def get_public_key(self) -> str:
        if not self._vk:
            return ""
        return self._vk.to_string().hex()
        
    def sign(self, data: bytes) -> str:
        if not self._sk:
            raise RuntimeError("Key not generated")
        # Pre-hash the data to ensure constant size
        import hashlib
        digest = hashlib.sha256(data).digest()
        sig = self._sk.sign(digest)
        return sig.hex()
        
    def verify(self, data: bytes, signature: str) -> bool:
        if not self._vk:
            return False
        import hashlib
        digest = hashlib.sha256(data).digest()
        try:
            return self._vk.verify(bytes.fromhex(signature), digest)
        except Exception:
            return False
            
    def get_key_id(self) -> str:
        return self._key_id
        
    def get_attestation(self) -> Dict[str, Any]:
        return {
            "signer_type": "SOFTWARE",
            "key_id": self._key_id,
            "attestation_available": False
        }

class WindowsTPMSigner(HardwareSigner):
    """Explicitly unsupported on Python prototype."""
    
    def __init__(self):
        self._key_id = f"wtpm-{uuid.uuid4()}"
        
    def generate_key(self) -> str:
        raise NotImplementedError("Windows TPM integration requires C++ CryptoAPI bindings not available in prototype")
        
    def get_public_key(self) -> str:
        return ""
        
    def sign(self, data: bytes) -> str:
        raise NotImplementedError("Windows TPM signing unavailable")
        
    def verify(self, data: bytes, signature: str) -> bool:
        return False
        
    def get_key_id(self) -> str:
        return self._key_id
        
    def get_attestation(self) -> Dict[str, Any]:
        return {
            "signer_type": "WINDOWS_TPM",
            "key_id": self._key_id,
            "attestation_available": False,
            "status": "UNAVAILABLE"
        }

class LinuxTPMSigner(HardwareSigner):
    """Stub for Linux native TPM implementation using tpm2-tss."""
    
    def __init__(self):
        self._key_id = f"ltpm-{uuid.uuid4()}"
        
    def generate_key(self) -> str:
        raise NotImplementedError("Linux TPM requires tpm2-tools execution context")
        
    def get_public_key(self) -> str:
        return ""
        
    def sign(self, data: bytes) -> str:
        raise NotImplementedError("Linux TPM signing unavailable")
        
    def verify(self, data: bytes, signature: str) -> bool:
        return False
        
    def get_key_id(self) -> str:
        return self._key_id
        
    def get_attestation(self) -> Dict[str, Any]:
        return {
            "signer_type": "LINUX_TPM",
            "key_id": self._key_id,
            "attestation_available": False,
            "status": "UNAVAILABLE"
        }

from typing import Any
