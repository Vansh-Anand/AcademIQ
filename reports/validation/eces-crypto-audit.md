# ECES Cryptographic Audit

## 1. Canonicalization (`CanonicalSerializer`)
- **What is Hashed**: The dictionary representation of the payload. Keys are sorted alphabetically (`sort_keys=True`). Nested objects are expanded. All whitespace stripped (`separators=(',', ':')`).
- **Domain Separation**: Included intrinsically by prepending a version identifier and a fixed record type in the root of the serialized event.
- **Reproducibility**: Identical events serialize precisely to the exact same UTF-8 byte stream. 

## 2. Hashing Engine (`HashProvider`)
- **Algorithm**: `blake3` if available natively, with a safe, logged fallback to `hashlib.sha256`.
- **Chain Semantics**: `current_hash = H(previous_hash || canonical(event))`. This creates a computationally unbreakable strictly causal chain.

## 3. TPM Hardware Signing (`HardwareSigner`)
- **What is Signed**: The `current_hash` of an `EvidenceRecord`. 
- **Sequence Protection**: By signing the chain hash rather than just the payload, the TPM attests not just to the event, but its strict temporal position.
- **Platform Limitations**: Hardware signers are completely stubbed on Windows. They raise `NotImplementedError` or use the fallback `SoftwareSigner` appropriately based on the initialization flags.

## 4. Tamper Validations
- **Payload Modification**: `EvidenceVerifier` correctly detects digest mismatch during re-hashing of the modified bytes.
- **Sequence Modification**: Dropped or reordered events break the `previous_hash` linkage, invalidating the entire subsequent chain.
- **Signature Modification**: Fails ECDSA `verify()` step explicitly.
