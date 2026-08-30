import argparse
import sys

from l6_eces.storage.sqlite_store import SQLiteEvidenceStore
from l6_eces.crypto.signer import SoftwareSigner
from l6_eces.forensics.verifier import EvidenceVerifier

def main():
    parser = argparse.ArgumentParser(description="AcademIQ ECES Chain Verification Tool")
    parser.add_argument("--database", required=True, help="Path to SQLite evidence database")
    parser.add_argument("--session", required=False, help="Verify records only for a specific session_id")
    args = parser.parse_args()
    
    store = SQLiteEvidenceStore(db_path=args.database)
    records = store.read_all()
    
    if args.session:
        # Filter evidence by session. Genesis has no session_id but is required for verification.
        # We assume genesis is needed for any chain validation.
        filtered = []
        for r in records:
            if r["_type"] == "genesis":
                filtered.append(r)
            else:
                if r["data"].get("session_id") == args.session:
                    filtered.append(r)
        records = filtered
        
    print(f"SESSION: {args.session if args.session else 'ALL'}\n")
    print(f"Records retrieved: {len(records)}\n")
    
    if not records:
        print("FINAL RESULT: INVALID (No records found)")
        sys.exit(1)
        
    # SoftwareSigner as a mock registry for verification (ephemeral)
    signer = SoftwareSigner()
    verifier = EvidenceVerifier(signer)
    
    result = verifier.verify_chain(records)
    
    # Map the granular EvidenceVerifier output to the requested format
    # link integrity = SEQUENCE_MISMATCH, CHAIN_BREAK
    # cryptographic integrity = GENESIS_HASH_MISMATCH, PAYLOAD_HASH_MISMATCH, EVENT_HASH_MISMATCH, SIGNATURE_INVALID
    
    link_integrity = "PASS"
    crypto_integrity = "PASS"
    
    if not result.valid:
        if result.failure_type in ["SEQUENCE_MISMATCH", "CHAIN_BREAK", "MISSING_GENESIS"]:
            link_integrity = "FAIL"
        elif result.failure_type in ["GENESIS_HASH_MISMATCH", "PAYLOAD_HASH_MISMATCH", "EVENT_HASH_MISMATCH", "SIGNATURE_INVALID"]:
            crypto_integrity = "FAIL"
        else:
            link_integrity = "FAIL"
            crypto_integrity = "FAIL"
            
    print(f"Records verified: {result.records_checked}\n")
    print(f"Link integrity: {link_integrity}")
    print(f"Cryptographic integrity: {crypto_integrity}\n")
    
    if result.valid:
        print("FINAL RESULT: VALID")
        sys.exit(0)
    else:
        print(f"Reason: {result.failure_type} at sequence {result.first_failure_sequence}")
        print("FINAL RESULT: INVALID")
        sys.exit(1)

if __name__ == "__main__":
    main()
