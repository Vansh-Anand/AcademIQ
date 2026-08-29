import abc
import hashlib
import time
from typing import Optional, Dict, Any
from pydantic import BaseModel

class AttestationEvidence(BaseModel):
    attestation_type: str
    platform: str
    measurement: str
    nonce: str
    timestamp: float
    certificate_chain_reference: Optional[str]
    quote_reference: Optional[str]
    verification_status: str

class ConfidentialComputeProvider(abc.ABC):
    """Abstract interface for Hardware Trusted Execution Environments."""

    @abc.abstractmethod
    def is_available(self) -> bool:
        pass

    @abc.abstractmethod
    def get_platform(self) -> str:
        pass

    @abc.abstractmethod
    def get_measurement(self) -> str:
        """Returns the hardware-backed measurement (MRTD/MRD) of the domain."""
        pass

    @abc.abstractmethod
    def get_attestation(self, nonce: str) -> AttestationEvidence:
        """Requests a cryptographically signed quote binding the measurement to the nonce."""
        pass


class IntelTDXProvider(ConfidentialComputeProvider):
    def is_available(self) -> bool:
        return False
    
    def get_platform(self) -> str:
        return "Intel TDX"
        
    def get_measurement(self) -> str:
        raise NotImplementedError("Intel TDX hardware unavailable in this environment.")
        
    def get_attestation(self, nonce: str) -> AttestationEvidence:
        raise NotImplementedError("Intel TDX attestation unavailable.")


class AMDSEVSNPProvider(ConfidentialComputeProvider):
    def is_available(self) -> bool:
        return False
    
    def get_platform(self) -> str:
        return "AMD SEV-SNP"
        
    def get_measurement(self) -> str:
        raise NotImplementedError("AMD SEV-SNP hardware unavailable in this environment.")
        
    def get_attestation(self, nonce: str) -> AttestationEvidence:
        raise NotImplementedError("AMD SEV-SNP attestation unavailable.")


class SimulationTEEProvider(ConfidentialComputeProvider):
    """Deterministic simulation provider for development and testing."""
    
    def __init__(self, simulated_measurement: str = "simulated_mrtd_hash"):
        self._measurement = simulated_measurement

    def is_available(self) -> bool:
        return True
    
    def get_platform(self) -> str:
        return "SIMULATION"
        
    def get_measurement(self) -> str:
        return self._measurement
        
    def get_attestation(self, nonce: str) -> AttestationEvidence:
        # Simulate a quote by hashing measurement + nonce
        quote = hashlib.sha256(f"{self._measurement}:{nonce}".encode()).hexdigest()
        
        return AttestationEvidence(
            attestation_type="SIMULATED_QUOTE",
            platform=self.get_platform(),
            measurement=self._measurement,
            nonce=nonce,
            timestamp=time.time(),
            certificate_chain_reference=None,
            quote_reference=quote,
            verification_status="PENDING"
        )
