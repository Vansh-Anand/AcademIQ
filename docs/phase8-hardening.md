# Phase 8 Hardening

Phase 8 implements the `l7_trust` layer to bootstrap AcademIQ into a Confidential Computing environment.

## Capabilities Detected
- **Intel TDX**: Scaffolding provided via `IntelTDXProvider`.
- **AMD SEV-SNP**: Scaffolding provided via `AMDSEVSNPProvider`.
- **Simulation**: Implemented via `SimulationTEEProvider`. 
*(Note: Windows development environments will correctly report native Linux TEEs as unavailable and fall back to Simulation).*

## Security Session
A full `SecuritySession` tracks:
- Start/End time
- Configuration Hash
- Model and Policy Versions
- Attestation State
- L1-L5 Events and Incidents
- Evidence Chain Reference

## Attestation Protocol
1. Host requests a challenge (nonce) from the Remote Verifier.
2. `ConfidentialComputeProvider` binds the `SecurityMeasurement` (hash of policies/models) to the nonce and generates a hardware quote.
3. `AttestationVerifier` validates the nonce freshness, measurement match, and signature validity before entering `HIGH_ASSURANCE` mode.
