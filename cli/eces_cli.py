import argparse
import sys
import json
import time
from typing import List

from l6_eces.chain.store import JsonlEvidenceStore
from l6_eces.crypto.hasher import HashProvider
from l6_eces.crypto.signer import SoftwareSigner
from l6_eces.forensics.verifier import EvidenceVerifier
from l6_eces.forensics.exporter import EvidenceExporter
from l6_eces.forensics.certificate import CertificateGenerator

def status(args):
    store = JsonlEvidenceStore()
    head = store.get_chain_head()
    if not head:
        print("ECES Chain: EMPTY")
        return
        
    print("=== ECES Chain Status ===")
    print(f"Chain ID: {head.chain_id}")
    print(f"Latest Sequence: {head.latest_sequence}")
    print(f"Head Hash: {head.latest_event_hash}")
    print(f"Last Updated: {head.updated_at} ns")
    
def verify(args):
    store = JsonlEvidenceStore()
    records = store.read_all()
    
    # We use SoftwareSigner here to hold the verification keys (mocking a registry)
    signer = SoftwareSigner()
    # In a real offline tool, you'd load public keys here. Since this is testing, 
    # we'll assume the verifier can't easily verify the signature if it wasn't the one who signed it 
    # (because it's an ephemeral key). We'll skip sig checking failure if it happens due to mock.
    
    verifier = EvidenceVerifier(signer)
    
    print(f"Loaded {len(records)} records.")
    start_time = time.time()
    result = verifier.verify_chain(records)
    elapsed = time.time() - start_time
    
    print("\n=== ECES Verification Result ===")
    print(f"Valid: {result.valid}")
    print(f"Records Checked: {result.records_checked}")
    if not result.valid:
        print(f"Failure Type: {result.failure_type}")
        print(f"Failed at Sequence: {result.first_failure_sequence}")
        print(f"Failed Event ID: {result.failure_event_id}")
        
    print(f"Time Taken: {elapsed:.4f} seconds")

def cmd_recover(args):
    store = JsonlEvidenceStore()
    from l6_eces.chain.store import EvidenceRecoveryManager
    manager = EvidenceRecoveryManager(store)
    head = manager.recover()
    if head:
        print(f"Recovered chain {head.chain_id} up to sequence {head.latest_sequence}")
    else:
        print("No chain to recover.")

def export(args):
    store = JsonlEvidenceStore()
    hasher = HashProvider()
    signer = SoftwareSigner()
    signer.generate_key()
    
    exporter = EvidenceExporter(store, hasher, signer)
    try:
        path = exporter.export_chain()
        print(f"Successfully exported chain to: {path}")
    except Exception as e:
        print(f"Export failed: {e}")

def certificate(args):
    store = JsonlEvidenceStore()
    records = store.read_all()
    if not records:
        print("No records available to certify.")
        return
        
    genesis = records[0]["data"]
    
    from l6_eces.chain.schemas import EvidenceManifest
    manifest = EvidenceManifest(
        package_id="live-cert-pkg",
        chain_id=genesis.get("chain_id"),
        incident_ids=[],
        sequence_start=0,
        sequence_end=len(records)-1,
        created_at=genesis.get("created_at"),
        exported_at=time.time_ns(),
        hash_algorithm="SHA-256",
        signature_algorithm="ECDSA-P256",
        signer_type="SOFTWARE",
        signer_key_id="live-key",
        redaction_mode="STANDARD",
        policy_version="1.0",
        model_versions=[],
        configuration_hash="CONFIG",
        event_count=len(records),
        package_hash="PENDING_EXPORT",
        verification_status="UNVERIFIED"
    )
    
    cert = CertificateGenerator.generate_certificate(
        manifest=manifest,
        operator_name=args.operator_name,
        operator_designation=args.operator_designation
    )
    
    print(cert)

def register_commands(subparsers):
    parser = subparsers.add_parser('eces', help='Phase 7: ECES commands')
    sub = parser.add_subparsers(dest='eces_cmd')
    
    # Status
    status_parser = sub.add_parser('status', help='View evidence chain head status')
    status_parser.set_defaults(func=status)
    
    # Verify
    verify_parser = sub.add_parser('verify', help='Verify chain integrity')
    verify_parser.set_defaults(func=verify)
    
    # Export
    export_parser = sub.add_parser('export', help='Export chain to forensic zip')
    export_parser.set_defaults(func=export)
    
    # Certificate
    cert_parser = sub.add_parser('certificate', help='Generate BSA Section 63 Certificate')
    cert_parser.add_argument('--operator-name', type=str, default="System Administrator")
    cert_parser.add_argument('--operator-designation', type=str, default="Security Officer")
    cert_parser.set_defaults(func=certificate)
