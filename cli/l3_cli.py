import argparse
import sys
import os
import subprocess

def register_commands(subparsers: argparse._SubParsersAction):
    l3_parser = subparsers.add_parser("l3", help="Layer 3 eBPF Validation Tools")
    l3_subparsers = l3_parser.add_subparsers(dest="l3_cmd")

    doctor_parser = l3_subparsers.add_parser("doctor", help="Run the L3 native Linux preflight checks")
    
def handle_l3_commands(args):
    if args.l3_cmd == "doctor":
        handle_l3_doctor(args)
    else:
        print("Invalid or missing l3 command.")
        sys.exit(1)

def handle_l3_doctor(args):
    print("Running L3 eBPF Native Preflight Validation...")
    if os.name == 'nt':
        print("[WARN] Running on Windows. AcademIQ L3 native validation requires a Linux host.")
        print("[WARN] The NativeEBpfCollector will gracefully fail-closed on this OS.")
        print("To run the full preflight, please execute this inside the Ubuntu deployment.")
    else:
        preflight_script = os.path.join(
            os.path.dirname(__file__), "..", "deployments", "linux-validation", "preflight.sh"
        )
        if os.path.exists(preflight_script):
            # Ensure it is executable
            os.chmod(preflight_script, 0o755)
            subprocess.run([preflight_script])
        else:
            print(f"[FAIL] Preflight script not found at {preflight_script}")
            sys.exit(1)
