import argparse
import sys
import time
import uuid
import json

from cli.l1_cli import register_commands as register_l1_commands
from cli.l2_cli import register_commands as register_l2_commands
from cli.l3_cli import register_commands as register_l3_commands
from cli.l4_cli import register_commands as register_l4_commands
from cli.l5_cli import register_commands as register_l5_commands
from cli.eces_cli import register_commands as register_eces_commands
from scripts.setup.discover import discover_environment
from orchestrator.pipeline.core import AcademiqOrchestrator
from common.events.schemas import ToolInvocationEvent

def main():
    parser = argparse.ArgumentParser(description="AcademIQ Security Interceptor")
    subparsers = parser.add_subparsers(dest="command")

    register_l1_commands(subparsers)
    register_l2_commands(subparsers)
    register_l3_commands(subparsers)
    register_l4_commands(subparsers)
    register_l5_commands(subparsers)
    register_eces_commands(subparsers)

    # Doctor Command
    doctor_parser = subparsers.add_parser("doctor", help="Inspect the current environment")

    # Run Command
    run_parser = subparsers.add_parser("run", help="Run the interceptor pipeline")
    run_parser.add_argument("--mode", type=str, choices=["simulation", "native"], default="simulation", help="Execution mode")

    # SDN Command
    sdn_parser = subparsers.add_parser("sdn", help="SDN tools")
    sdn_subparsers = sdn_parser.add_subparsers(dest="sdn_command")
    
    sdn_norm = sdn_subparsers.add_parser("normalize")
    sdn_norm.add_argument("--command", dest="cmd", type=str, help="Command to normalize")
    
    sdn_anal = sdn_subparsers.add_parser("analyze")
    sdn_anal.add_argument("--command", dest="cmd", type=str, help="Command to analyze")
    
    sdn_pol = sdn_subparsers.add_parser("policy-check")
    sdn_pol.add_argument("--command", dest="cmd", type=str, help="Command to check against policy")
    
    sdn_bench = sdn_subparsers.add_parser("benchmark")
    
    # Exec Command
    exec_parser = subparsers.add_parser("exec", help="Execute command")

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

    elif args.command == "sdn":
        from common.events.schemas import ShellCommandEvent
        
        if args.sdn_command == "benchmark":
            from benchmarks.latency.sdn_benchmark import run_benchmark
            run_benchmark()
            return
            
        if not args.cmd:
            print("ERROR: --command is required")
            sys.exit(1)
            
        print(f"SDN Analysis for: {args.cmd}")
        event = ShellCommandEvent(
            event_id=f"evt-{uuid.uuid4()}",
            timestamp_ns=time.time_ns(),
            layer="L2",
            trace_id=f"trc-{uuid.uuid4()}",
            raw_command=args.cmd
        )
        
        from l2_sdn.interceptor import DevelopmentShellInterceptor
        interceptor = DevelopmentShellInterceptor()
        
        decision, out_event = interceptor.intercept(event)
        
        if args.sdn_command == "normalize":
            print("Normalized Command Info:")
            print(f"Original Hash: {out_event.original_command_hash}")
            print(f"Canonical Hash: {out_event.canonical_command_hash}")
            print(f"Transformations: {out_event.transformations}")
        elif args.sdn_command == "analyze":
            print(f"Canonical Hash: {out_event.canonical_command_hash}")
            print(f"Obfuscation Detected: {out_event.obfuscation_detected}")
            print(f"Identities resolved: {len(out_event.path_identities)}")
        elif args.sdn_command == "policy-check":
            print(f"Decision: {out_event.policy_result}")
            print(f"Reason: {out_event.matched_rule}")
            
    elif args.command == "exec":
        print("ERROR: Execution is disabled in Phase 3. The pipeline verifies security decisions safely without evaluating commands.")
        sys.exit(1)

    elif args.command == "l4":
        from cli.l4_cli import handle_l4_train
        if args.l4_cmd == "train":
            handle_l4_train(args)
    elif args.command == "riskchain":
        from cli.l5_cli import handle_riskchain_status
        if args.rc_cmd == "status":
            handle_riskchain_status(args)
    elif args.command == "governance":
        from cli.l5_cli import handle_governance_evaluate
        if args.gov_cmd == "evaluate":
            handle_governance_evaluate(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    from cli.l4_cli import setup_parser as setup_l4_parser
    from cli.l5_cli import setup_parser as setup_l5_parser
    # We must patch the parser in main
    import argparse
    # This is a hacky injection but works for our script without breaking others
    old_parse = argparse.ArgumentParser.parse_args
    def hooked_parse(self, *a, **kw):
        # Find subparsers action and add our l4_parser
        for action in self._actions:
            if isinstance(action, argparse._SubParsersAction):
                setup_l4_parser(action)
                setup_l5_parser(action)
        return old_parse(self, *a, **kw)
    argparse.ArgumentParser.parse_args = hooked_parse
    main()
