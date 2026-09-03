from common.events.schemas import ToolInvocationEvent, ShellCommandEvent, DivergenceEvent
from common.schemas.security import SecurityDecision, DecisionEnum
import time
import uuid

from l6_eces.crypto.hasher import HashProvider
from l6_eces.crypto.signer import SoftwareSigner
from l6_eces.storage.sqlite_store import SQLiteEvidenceStore
from l6_eces.chain.writer import EvidenceChainWriter
from l6_eces.redaction.policy import EvidenceRedactionPolicy

class AcademiqOrchestrator:
    def __init__(self, mode: str = "simulation", l3_collector: 'typing.Any' = None):
        import typing
        self.mode = mode
        self.session_id = str(uuid.uuid4())
        
        # ECES setup
        self.eces_store = SQLiteEvidenceStore()
        self.eces_hasher = HashProvider()
        self.eces_signer = SoftwareSigner()
        self.eces_signer.generate_key()
        self.eces_writer = EvidenceChainWriter(self.eces_store, self.eces_hasher, self.eces_signer)
        self.eces_redactor = EvidenceRedactionPolicy(mode="STANDARD")
        
        # Injected dependencies
        self.l3_collector = l3_collector
        self.l3_events_processed = []
        self.l3_anomalies = []
        self.correlation_manager = None
        
        if self.l3_collector and hasattr(self.l3_collector, "register_callback"):
            from l3_ebpf.userspace.correlation import ExecutionCorrelationManager
            self.correlation_manager = ExecutionCorrelationManager()
            self.l3_collector.register_callback(self._on_l3_event)
        
        print(f"[Orchestrator] Initialized in {self.mode.upper()} mode. Session: {self.session_id}")

    def _on_l3_event(self, event):
        self.l3_events_processed.append(event)
        if self.correlation_manager:
            correlated, anomaly = self.correlation_manager.correlate_syscall(event)
            if not correlated:
                self.l3_anomalies.append(anomaly)

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
            
            # Extract the primary argument for the mock token stream (first value in dict or empty string)
            arg_val = list(event.arguments.values())[0] if event.arguments else ""
            mock_token_stream = f'{event.tool_name}("{arg_val}")'
            print(f"L1 GCD -> Checking tool invocation: {mock_token_stream}")
            
            # Very basic check: does it match any valid prefix in the automaton?
            is_valid = pda.is_valid_prefix(mock_token_stream, pda.initial_config)
            
            if not is_valid:
                print("L1 GCD -> [BLOCK] Policy violation detected before generation.")
                decision_obj = SecurityDecision(
                    decision=DecisionEnum.BLOCK,
                    reason_codes=["GCD_POLICY_VIOLATION"],
                    risk_score=100.0,
                    confidence=1.0,
                    source_layers=["L1"],
                    related_event_ids=[event.event_id],
                    timestamp_ns=time.time_ns()
                )
                # Record the rejected event and decision
                redacted_event = self.eces_redactor.redact(event.model_dump())
                self.eces_writer.append_event(type(event)(**redacted_event), source_layer="L1")
                
                from common.events.schemas import EnforcementEvent
                enf_event = EnforcementEvent(
                    event_type="Enforcement",
                    event_id=f"enf-{uuid.uuid4()}",
                    timestamp_ns=time.time_ns(),
                    trace_id=event.trace_id,
                    layer="L1",
                    incident_id=f"inc-{uuid.uuid4()}",
                    cgroup_id="test",
                    action=decision_obj.decision.value,
                    reason=",".join(decision_obj.reason_codes),
                    risk_score=decision_obj.risk_score,
                    trigger_event_ids=decision_obj.related_event_ids,
                    success=True,
                    operator_source="SYSTEM"
                )
                self.eces_writer.append_event(enf_event, source_layer="L1")
                return decision_obj
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
        from l2_sdn.interceptor import DevelopmentShellInterceptor
        from common.events.schemas import ShellCommandEvent
        
        try:
            l2_interceptor = DevelopmentShellInterceptor()
            # Construct a mock shell command based on L1's output
            # For example, if L1 allowed read_file("/etc/passwd"), the underlying tool
            # execution might correspond to a shell command like `cat /etc/passwd`
            # For this test, we construct the shell equivalent
            arg_val = list(event.arguments.values())[0] if event.arguments else ""
            mock_shell_cmd = arg_val if event.tool_name == "execute_command" else f"cat {arg_val}"
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
            
            if l2_decision == "BLOCK":
                print(f"L2 SDN -> [BLOCK] Semantic violation detected: {locked_ast.matched_rule}")
                # We stop the pipeline immediately. L1 ALLOW + L2 BLOCK -> NO EXECUTION.
                return SecurityDecision(
                    decision=DecisionEnum.BLOCK,
                    reason_codes=[locked_ast.matched_rule or "SDN_BLOCK"],
                    risk_score=100.0,
                    confidence=1.0,
                    source_layers=["L1", "L2"],
                    related_event_ids=[event.event_id, shell_event.event_id],
                    timestamp_ns=time.time_ns()
                )
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

        if self.l3_collector:
            print("L3 eBPF -> Using injected collector for telemetry replay. Skipping mock pipeline.")
            # For replay scenarios, L4 and L5 are currently unavailable in the native stream
            decision = SecurityDecision(
                decision=DecisionEnum.ALLOW,
                reason_codes=[],
                risk_score=0.0,
                confidence=1.0,
                source_layers=["L1", "L2"],
                related_event_ids=[event.event_id, shell_event.event_id],
                timestamp_ns=time.time_ns()
            )
            print(f"--- Event Processing Complete. Final Decision: {decision.decision.value} ---")
            return decision

        print("L3 eBPF -> Synthesizing mock telemetry...")
        
        # Simulate Divergence Event
        from common.events.schemas import DivergenceResult, WindowQuality
        
        mock_quality = WindowQuality(
            event_count=100, expected_count=100, dropped_events=0,
            ordering_valid=True, timestamp_quality=1.0, hpc_coverage=1.0, quality_score=1.0
        )
        mock_result = DivergenceResult(
            score=0.1, confidence=0.99, siamese_score=0.1, isolation_score=0.1, ece_threshold=0.8,
            above_threshold=False, window_quality=mock_quality, hpc_available=True,
            model_version="1.0", ece_version="1.0", reason_codes=[]
        )
        
        div_event = DivergenceEvent(
            event_id=f"div-{uuid.uuid4()}",
            timestamp_ns=time.time_ns(),
            layer="L4",
            trace_id=event.trace_id,
            simulation=(self.mode == "simulation"),
            agent_id="test-agent",
            session_id=self.session_id,
            window_id="win-1",
            window_start=time.time_ns(),
            window_end=time.time_ns(),
            syscall_count=15,
            result=mock_result,
            decision="ALLOW"
        )
        print(f"L4 Divergence -> Score: {div_event.result.score}")

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
            event_type="Enforcement",
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
