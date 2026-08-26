from common.events.schemas import ToolInvocationEvent, ShellCommandEvent, DivergenceEvent
from common.schemas.security import SecurityDecision, DecisionEnum
import time
import uuid

class AcademiqOrchestrator:
    def __init__(self, mode: str = "simulation"):
        self.mode = mode
        self.session_id = str(uuid.uuid4())
        print(f"[Orchestrator] Initialized in {self.mode.upper()} mode. Session: {self.session_id}")

    def process_event(self, event) -> SecurityDecision:
        print(f"\n--- Processing Event: {event.event_type} (ID: {event.event_id}) ---")
        print("L1 GCD -> Initializing Compiler...")
        from l1_gcd.compiler import YamlGCDCompiler
        from l1_gcd.automaton import PushdownAutomaton
        import yaml
        
        try:
            with open("config/policies/gcd.yaml", "r") as f:
                policy_dict = yaml.safe_load(f)
            
            compiler = YamlGCDCompiler()
            grammar = compiler.compile_policy(policy_dict)
            pda = PushdownAutomaton(grammar)
            
            # Check if the requested tool in the event is a valid prefix
            mock_token_stream = f'{event.tool_name}("{event.arguments.get("path", "")}")'
            print(f"L1 GCD -> Checking tool invocation: {mock_token_stream}")
            
            # Very basic check: does it match any valid prefix in the automaton?
            is_valid = pda.is_valid_prefix(mock_token_stream, pda.initial_config)
            
            if not is_valid:
                print("L1 GCD -> [BLOCK] Policy violation detected before generation.")
                return SecurityDecision(
                    decision=DecisionEnum.BLOCK,
                    reason_codes=["GCD_POLICY_VIOLATION"],
                    risk_score=100.0,
                    confidence=1.0,
                    source_layers=["L1"],
                    related_event_ids=[event.event_id],
                    timestamp_ns=time.time_ns()
                )
            else:
                print("L1 GCD -> [ALLOW] Token sequence is legal under CFG.")
        except Exception as e:
            print(f"L1 GCD -> [BLOCK] Error loading/compiling policy: {e}")
            return SecurityDecision(
                decision=DecisionEnum.BLOCK,
                reason_codes=["GCD_DECODING_ERROR"],
                risk_score=100.0,
                confidence=1.0,
                source_layers=["L1"],
                related_event_ids=[event.event_id],
                timestamp_ns=time.time_ns()
            )
            
        print("L2 SDN -> Interface bypassed (mock)")
        print("L3 eBPF -> Synthesizing mock telemetry...")
        
        # Simulate Divergence Event
        div_event = DivergenceEvent(
            event_id=f"div-{uuid.uuid4()}",
            timestamp_ns=time.time_ns(),
            layer="L4",
            trace_id=event.trace_id,
            simulation=(self.mode == "simulation"),
            divergence_score=0.1,
            features_analyzed=15
        )
        print(f"L4 Divergence -> Score: {div_event.divergence_score}")

        print("L5 RiskChain -> Generating Decision...")
        
        # Simulate final decision
        decision = SecurityDecision(
            decision=DecisionEnum.ALLOW,
            reason_codes=["MOCK_SAFE_TEST"],
            risk_score=15.0,
            confidence=0.99,
            source_layers=["L1", "L2", "L3", "L4", "L5"],
            related_event_ids=[event.event_id, div_event.event_id],
            timestamp_ns=time.time_ns()
        )

        print("Enforcement -> None (ALLOW)")
        print("ECES -> Generating mock hash chain record...")
        print(f"--- Event Processing Complete. Final Decision: {decision.decision.value} ---")
        return decision
