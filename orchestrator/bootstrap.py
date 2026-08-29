from typing import Optional
from ..l7_trust.detector import ConfidentialComputingDetector
from ..l7_trust.tee.provider import ConfidentialComputeProvider, SimulationTEEProvider, IntelTDXProvider, AMDSEVSNPProvider
from ..l7_trust.measurement.manifest import SecurityArtifactManifest, MeasurementGenerator, SecurityMeasurement
from ..l6_eces.crypto.signer import HardwareSigner

class SecurityBootstrap:
    """Bootstraps the trusted execution environment and verifies security boundaries."""
    
    def __init__(self, mode: str = "STANDARD"):
        self.mode = mode
        
    def bootstrap(self, manifest: SecurityArtifactManifest, signer: HardwareSigner) -> SecurityMeasurement:
        capabilities = ConfidentialComputingDetector.detect()
        
        provider: ConfidentialComputeProvider
        if capabilities.tdx_available:
            provider = IntelTDXProvider()
        elif capabilities.sev_snp_available:
            provider = AMDSEVSNPProvider()
        else:
            provider = SimulationTEEProvider(MeasurementGenerator.generate_manifest_hash(manifest))
            
        if self.mode == "HIGH_ASSURANCE":
            if not capabilities.attestation_available:
                raise RuntimeError("HIGH_ASSURANCE requires hardware TEE (TDX/SEV-SNP). Attestation unavailable.")
            if not signer.hardware_backed:
                raise RuntimeError("HIGH_ASSURANCE requires hardware-backed TPM signing.")
                
        # Simulate/generate measurement
        if isinstance(provider, SimulationTEEProvider):
            measurement = MeasurementGenerator.create_software_measurement(manifest)
        else:
            # Native would interact with /dev/tdx_guest or similar
            raise NotImplementedError("Native hardware measurement generation not fully implemented")
            
        return measurement
