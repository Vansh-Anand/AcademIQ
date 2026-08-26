from common.events.schemas import ToolInvocationEvent, ShellCommandEvent, DivergenceEvent
from common.schemas.security import SecurityDecision, DecisionEnum
import time
import uuid

from l6_eces.crypto.hasher import HashProvider
from l6_eces.crypto.signer import SoftwareSigner
from l6_eces.chain.store import EvidenceStore
from l6_eces.chain.writer import EvidenceChainWriter
from l6_eces.redaction.policy import EvidenceRedactionPolicy

class AcademiqOrchestrator:
    def __init__(self, mode: str = "simulation"):
        self.mode = mode
        self.session_id = str(uuid.uuid4())
        
        # ECES setup
        self.eces_store = EvidenceStore()
        self.eces_hasher = HashProvider()
        self.eces_signer = SoftwareSigner()
        self.eces_signer.generate_key()
        self.eces_writer = EvidenceChainWriter(self.eces_store, self.eces_hasher, self.eces_signer)
        self.eces_redactor = EvidenceRedactionPolicy(mode="STANDARD")
        
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
            
        print("L2 SDN -> Initializing Interceptor...")
        from l2_sdn.interceptor import L2Interceptor
        from common.events.schemas import ShellCommandEvent
        
        try:
            l2_interceptor = L2Interceptor()
            # Construct a mock shell command based on L1's output
            # For example, if L1 allowed read_file("/etc/passwd"), the underlying tool
            # execution might correspond to a shell command like `cat /etc/passwd`
            # For this test, we construct the shell equivalent
            mock_shell_cmd = f"cat {event.arguments.get('path', '')}"
            print(f"L2 SDN -> Intercepting shell payload: {mock_shell_cmd}")
            
            shell_event = ShellCommandEvent(
                event_id=f"sh-{uuid.uuid4()}",
                timestamp_ns=time.time_ns(),
                trace_id=event.trace_id,
                layer="L2",
                raw_command=mock_shell_cmd
            )
            
            # Persist L1 and L2 events
            redacted_event = self.eces_redactor.redact(event.model_dump())
            event_copy = type(event)(**redacted_event)
            self.eces_writer.append_event(event_copy, source_layer="L1")
            
            redacted_shell = self.eces_redactor.redact(shell_event.model_dump())
            shell_copy = ShellCommandEvent(**redacted_shell)
            self.eces_writer.append_event(shell_copy, source_layer="L2")
            
            l2_decision, locked_ast = l2_interceptor.intercept(shell_event)
            
            if l2_decision.decision == DecisionEnum.BLOCK:
                print(f"L2 SDN -> [BLOCK] Semantic violation detected: {l2_decision.reason_codes[0]}")
                # We stop the pipeline immediately. L1 ALLOW + L2 BLOCK -> NO EXECUTION.
                return l2_decision
            else:
                print("L2 SDN -> [ALLOW] Semantic analysis passed.")
                
        except Exception as e:
            print(f"L2 SDN -> [BLOCK] Processing Error: {e}")
            return SecurityDecision(
                decision=DecisionEnum.BLOCK,
                reason_codes=["SDN_PROCESSING_ERROR"],
                risk_score=100.0,
                confidence=1.0,
                source_layers=["L2"],
                related_event_ids=[event.event_id],
                timestamp_ns=time.time_ns()
            )

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
        
        # Persist L4 Divergence
        redacted_div = self.eces_redactor.redact(div_event.model_dump())
        div_copy = DivergenceEvent(**redacted_div)
        self.eces_writer.append_event(div_copy, source_layer="L4")

        print("Enforcement -> None (ALLOW)")
        print("ECES -> Generating hash chain record for decision...")
        
        # We can mock a RiskChainEvent or EnforcementEvent wrapping the decision
        from common.events.schemas import EnforcementEvent
        enf_event = EnforcementEvent(
            event_id=f"enf-{uuid.uuid4()}",
            timestamp_ns=time.time_ns(),
            trace_id=event.trace_id,
            layer="L5",
            incident_id=f"inc-{uuid.uuid4()}",
            cgroup_id="test",
            action=decision.decision.value,
            reason=",".join(decision.reason_codes),
            risk_score=decision.risk_score,
            trigger_event_ids=decision.related_event_ids,
            success=True,
            operator_source="SYSTEM"
        )
        self.eces_writer.append_event(enf_event, source_layer="L5")
        
        print(f"--- Event Processing Complete. Final Decision: {decision.decision.value} ---")
        return decision
