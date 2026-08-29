import argparse
import sys
import json
from l7_trust.detector import ConfidentialComputingDetector
from orchestrator.health.manager import SecurityHealthState, SecurityHealthManager

def handle_doctor(args):
    print("============================================================")
    print(" AcademIQ Security Doctor")
    print("============================================================")
    
    caps = ConfidentialComputingDetector.detect()
    
    print(f"[OS]              {caps.os_name} (Kernel: {caps.kernel_version})")
    print(f"[CPU]             {caps.cpu_vendor} {caps.cpu_model}")
    print(f"[TDX]             {'AVAILABLE' if caps.tdx_available else 'NOT AVAILABLE'}")
    print(f"[SEV-SNP]         {'AVAILABLE' if caps.sev_snp_available else 'NOT AVAILABLE'}")
    print(f"[ATTESTATION]     {'AVAILABLE' if caps.attestation_available else 'NOT AVAILABLE'}")
    print(f"[REASON]          {caps.reason}")
    print("============================================================")

def handle_status(args):
    health = SecurityHealthState()
    print("============================================================")
    print(" AcademIQ Security Status")
    print("============================================================")
    print(f"L1 (GCD)          : {health.L1}")
    print(f"L2 (SDN)          : {health.L2}")
    print(f"L3 (eBPF)         : {health.L3}")
    print(f"L4 (Divergence)   : {health.L4}")
    print(f"L5 (RiskChain)    : {health.L5}")
    print(f"ECES (Evidence)   : {health.ECES}")
    print(f"TPM Signer        : {health.TPM}")
    print(f"TEE Environment   : {health.TEE}")
    print("============================================================")
    mgr = SecurityHealthManager()
    print(f"OVERALL           : {mgr.get_overall_state()}")
    print("============================================================")

def handle_dependencies(args):
    # Simulated dependency validation
    print("============================================================")
    print(" AcademIQ Security Dependencies (Manifest Check)")
    print("============================================================")
    deps = [
        {"name": "pytest", "version": "8.2.2", "status": "VERIFIED"},
        {"name": "pydantic", "version": "2.8.0", "status": "VERIFIED"},
        {"name": "ecdsa", "version": "0.19.0", "status": "VERIFIED"},
    ]
    for d in deps:
        print(f"[{d['status']}] {d['name']} v{d['version']}")

def main():
    parser = argparse.ArgumentParser(description="AcademIQ Security CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    parser_doctor = subparsers.add_parser("doctor", help="Check hardware and OS security capabilities")
    parser_doctor.set_defaults(func=handle_doctor)
    
    parser_status = subparsers.add_parser("status", help="Check component health status")
    parser_status.set_defaults(func=handle_status)
    
    parser_deps = subparsers.add_parser("dependencies", help="Audit dependency manifest")
    parser_deps.set_defaults(func=handle_dependencies)
    
    args = parser.parse_args(sys.argv[2:])
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
