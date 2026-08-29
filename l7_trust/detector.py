import platform
import os
import subprocess
from pydantic import BaseModel
from typing import Optional

class PlatformCapabilities(BaseModel):
    os_name: str
    cpu_vendor: str
    cpu_model: str
    kernel_version: str
    tdx_available: bool
    sev_snp_available: bool
    attestation_available: bool
    reason: str

class ConfidentialComputingDetector:
    """Detects available hardware TEE and attestation capabilities."""
    
    @staticmethod
    def detect() -> PlatformCapabilities:
        os_name = platform.system()
        processor = platform.processor()
        release = platform.release()
        
        # Safe default values
        cpu_vendor = "Unknown"
        cpu_model = processor
        tdx = False
        sev = False
        attestation = False
        reason = "Platform capabilities not assessed."

        if os_name == "Windows":
            reason = "Windows environment detected. Native Linux TEEs (TDX/SEV-SNP) are NOT AVAILABLE and NOT EXECUTABLE."
            # We explicitly do not fabricate Windows hardware capabilities.
        elif os_name == "Linux":
            # Attempt basic vendor detection
            try:
                with open("/proc/cpuinfo", "r") as f:
                    content = f.read()
                    if "GenuineIntel" in content:
                        cpu_vendor = "Intel"
                        if "tdx_guest" in content:
                            tdx = True
                    elif "AuthenticAMD" in content:
                        cpu_vendor = "AMD"
                        if "sev_snp" in content:
                            sev = True
            except Exception:
                reason = "Could not read /proc/cpuinfo."
            
            if tdx or sev:
                attestation = True
                reason = "Native Linux TEE detected."
            else:
                reason = "Linux detected, but CPU does not expose TDX or SEV-SNP to this environment."
        
        return PlatformCapabilities(
            os_name=os_name,
            cpu_vendor=cpu_vendor,
            cpu_model=cpu_model,
            kernel_version=release,
            tdx_available=tdx,
            sev_snp_available=sev,
            attestation_available=attestation,
            reason=reason
        )
