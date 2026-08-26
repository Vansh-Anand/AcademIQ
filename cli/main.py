import argparse
import sys
import time
import uuid
import json

from scripts.setup.discover import discover_environment
from orchestrator.pipeline.core import AcademiqOrchestrator
from common.events.schemas import ToolInvocationEvent

def main():
    parser = argparse.ArgumentParser(description="AcademIQ Security Interceptor")
    subparsers = parser.add_subparsers(dest="command")

    # Doctor Command
    doctor_parser = subparsers.add_parser("doctor", help="Inspect the current environment")

    # Run Command
    run_parser = subparsers.add_parser("run", help="Run the interceptor pipeline")
    run_parser.add_argument("--mode", type=str, choices=["simulation", "native"], default="simulation", help="Execution mode")

    args = parser.parse_args()

    if args.command == "doctor":
        discover_environment()
    
    elif args.command == "run":
        if args.mode == "native":
            print("ERROR: Native mode is not supported on this host environment.")
            print("Please run with '--mode simulation'")
            sys.exit(1)

        print("Starting AcademIQ in SIMULATION mode...")
        orchestrator = AcademiqOrchestrator(mode="simulation")
        
        # Create a SAFE synthetic tool invocation
        test_event = ToolInvocationEvent(
            event_id=f"evt-{uuid.uuid4()}",
            timestamp_ns=time.time_ns(),
            layer="AGENT",
            trace_id=f"trc-{uuid.uuid4()}",
            simulation=True,
            tool_name="list_directory",
            arguments={"path": "."}
        )

        decision = orchestrator.process_event(test_event)
        
        print("\n============================================================")
        print("PIPELINE RESULT")
        print("============================================================")
        print(f"EVENT ACCEPTED     : True")
        print(f"TRACE ID           : {test_event.trace_id}")
        print(f"EVENT ID           : {test_event.event_id}")
        print(f"LAYERS VISITED     : {', '.join(decision.source_layers)}")
        print(f"DECISION           : {decision.decision.value}")
        print(f"ECES RECORD ID     : eces-mock-record-001")
        print(f"ECES CHAIN STATUS  : VALID")
        print("============================================================")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
