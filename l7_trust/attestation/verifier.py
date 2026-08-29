import time
import hashlib
from typing import Optional, Dict
from pydantic import BaseModel
from ..tee.provider import AttestationEvidence, ConfidentialComputeProvider

class AttestationChallenge(BaseModel):
    challenge_id: str
    nonce: str
    issued_at: float
    expires_at: float
    verifier_id: str

class AttestationResult(BaseModel):
    valid: bool
    platform: str
    measurement_match: bool
    fresh: bool
    signature_valid: bool
    policy_match: bool
    failure_reason: Optional[str]

class AttestationEvent(BaseModel):
    event_id: str
    attestation_id: str
    platform: str
    measurement: str
    status: str
    timestamp: float
    security_mode: str
    failure_reason: Optional[str]

class AttestationVerifier:
    """Verifies TEE attestation evidence against expected measurements and freshness requirements."""
    
    def __init__(self, expected_measurement: str, max_age_seconds: int = 300):
        self.expected_measurement = expected_measurement
        self.max_age_seconds = max_age_seconds
        self._active_challenges: Dict[str, AttestationChallenge] = {}

    def create_challenge(self, verifier_id: str = "academiq-host") -> AttestationChallenge:
        import uuid
        nonce = hashlib.sha256(os.urandom(32)).hexdigest()
        now = time.time()
        challenge = AttestationChallenge(
            challenge_id=str(uuid.uuid4()),
            nonce=nonce,
            issued_at=now,
            expires_at=now + self.max_age_seconds,
            verifier_id=verifier_id
        )
        self._active_challenges[nonce] = challenge
        return challenge

    def verify(self, evidence: AttestationEvidence, challenge_nonce: str) -> AttestationResult:
        now = time.time()
        
        # 1. Freshness check
        if challenge_nonce not in self._active_challenges:
            return AttestationResult(
                valid=False, platform=evidence.platform, measurement_match=False,
                fresh=False, signature_valid=False, policy_match=False,
                failure_reason="Challenge nonce not found or expired."
            )
            
        challenge = self._active_challenges[challenge_nonce]
        if now > challenge.expires_at:
            del self._active_challenges[challenge_nonce]
            return AttestationResult(
                valid=False, platform=evidence.platform, measurement_match=False,
                fresh=False, signature_valid=False, policy_match=False,
                failure_reason="Challenge expired."
            )
            
        if evidence.nonce != challenge_nonce:
            return AttestationResult(
                valid=False, platform=evidence.platform, measurement_match=False,
                fresh=False, signature_valid=False, policy_match=False,
                failure_reason="Evidence nonce does not match challenge nonce."
            )
            
        del self._active_challenges[challenge_nonce]
        
        # 2. Measurement check
        measurement_match = (evidence.measurement == self.expected_measurement)
        if not measurement_match:
            return AttestationResult(
                valid=False, platform=evidence.platform, measurement_match=False,
                fresh=True, signature_valid=False, policy_match=False,
                failure_reason=f"Measurement mismatch. Expected {self.expected_measurement}, got {evidence.measurement}"
            )
            
        # 3. Signature check (Simulated)
        if evidence.attestation_type == "SIMULATED_QUOTE":
            expected_quote = hashlib.sha256(f"{evidence.measurement}:{challenge_nonce}".encode()).hexdigest()
            signature_valid = (evidence.quote_reference == expected_quote)
        else:
            # Native HW signature verification would go here using remote attestation service
            signature_valid = False
            
        if not signature_valid:
            return AttestationResult(
                valid=False, platform=evidence.platform, measurement_match=True,
                fresh=True, signature_valid=False, policy_match=False,
                failure_reason="Invalid hardware signature / quote reference."
            )
            
        return AttestationResult(
            valid=True, platform=evidence.platform, measurement_match=True,
            fresh=True, signature_valid=True, policy_match=True,
            failure_reason=None
        )

import os
