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
        print("L1 GCD -> Interface bypassed (mock)")
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
