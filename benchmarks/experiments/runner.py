import time
from typing import Optional
from benchmarks.experiments.models import ScenarioDefinition, ExperimentResult, LayerOutcomes, LayerOutcome
from orchestrator.pipeline.core import AcademiqOrchestrator
from common.schemas.security import DecisionEnum

class ExperimentHarness:
    """
    Reusable experiment infrastructure to execute a ScenarioDefinition end-to-end
    through the existing AcademIQ security pipeline.
    """
    def __init__(self, orchestrator: Optional[AcademiqOrchestrator] = None):
        # Allow dependency injection of the orchestrator, or instantiate a new one
        self.orchestrator = orchestrator or AcademiqOrchestrator(mode="simulation")
        from l5_riskchain.correlation.cross_session import CrossSessionReplayDetector
        self.cross_session_detector = CrossSessionReplayDetector(window_seconds=3600, repeat_threshold=2, coordinated_threshold=3, risk_threshold=0.5)

    def run_scenario(self, scenario: ScenarioDefinition) -> ExperimentResult:
        start_ns = time.perf_counter_ns()
        
        result = ExperimentResult(
            scenario_id=scenario.scenario_id,
            start_timestamp_ns=start_ns,
            end_timestamp_ns=0,
            total_latency_ns=0,
            attack_blocked=False,
            attack_success=False
        )

        final_decision = None
        stopping_layer = None
        
        try:
            # Check for telemetry injection
            if scenario.telemetry_trace:
                from l3_ebpf.userspace.collector import SimulatedL3Collector
                from l3_ebpf.namespace.scope import AgentScopeManager
                from l3_ebpf.userspace.health import TelemetryHealthMonitor
                from l3_ebpf.userspace.correlation import ExecutionCorrelationManager
                
                scope = AgentScopeManager()
                # Use default test agent values expected by tests/fixtures
                scope.register_agent("test_agent_1", 1000, 1234)
                
                collector = SimulatedL3Collector(scope, TelemetryHealthMonitor(), scenario.telemetry_trace)
                self.orchestrator.l3_collector = collector
                self.orchestrator.correlation_manager = ExecutionCorrelationManager()
                
                if scenario.metadata.get("seed_l2_commands"):
                    from l2_sdn.events import NormalizedCommandEvent
                    for cmd in scenario.metadata["seed_l2_commands"]:
                        self.orchestrator.correlation_manager.register_l2_decision(NormalizedCommandEvent(
                            event_id="dummy", session_id="dummy", trace_id="dummy",
                            original_command_hash="dummy", canonical_command_hash="dummy",
                            agent_id="test_agent_1", normalized_command=cmd, passes_applied=1, policy_result="ALLOW"
                        ))

                if hasattr(collector, "register_callback"):
                    collector.register_callback(self.orchestrator._on_l3_event)

            # Currently, the orchestrator primarily takes an agent event and handles the full pipeline mock.
            # If a scenario defines agent_events, we run them through the orchestrator.
            for event in scenario.agent_events:
                decision = self.orchestrator.process_event(event)
                final_decision = decision
                
                # If the pipeline blocks at any point, it stops execution
                if decision.decision == DecisionEnum.BLOCK:
                    stopping_layer = decision.source_layers[-1] if decision.source_layers else "UNKNOWN"
                    break

            # If shell_events exist, but no agent_events were provided, we could inject directly to L2.
            # (Extensibility for future direct L2 tests)
            if not scenario.agent_events and scenario.shell_events:
                from l2_sdn.interceptor import DevelopmentShellInterceptor
                interceptor = DevelopmentShellInterceptor()
                for shell_event in scenario.shell_events:
                    decision, _ = interceptor.intercept(shell_event)
                    # Convert L2 decision string to DecisionEnum for logic
                    if decision == "BLOCK":
                        final_decision = type("MockDecision", (), {"decision": DecisionEnum.BLOCK, "source_layers": ["L2"], "risk_score": 100, "confidence": 1.0, "reason_codes": []})()
                        stopping_layer = "L2"
                        break
                    else:
                        final_decision = type("MockDecision", (), {"decision": DecisionEnum.ALLOW, "source_layers": ["L2"], "risk_score": 0, "confidence": 1.0, "reason_codes": []})()

            if scenario.risk_nodes:
                from l5_riskchain.graph.risk_graph import RiskChainGraph
                from l5_riskchain.correlation.engine import RiskCorrelationEngine
                from l5_riskchain.bayesian.model import BayesianRiskModel
                from l5_riskchain.governance.fuzzy_engine import GovernanceEngine
                from l5_riskchain.graph.analyzer import RiskPathAnalyzer

                graph = RiskChainGraph(agent_id="test_agent")
                correlator = RiskCorrelationEngine()
                bayes = BayesianRiskModel("config/policies/bayesian.yaml")
                gov = GovernanceEngine()
                analyzer = RiskPathAnalyzer()
                
                # Insert nodes
                for n in scenario.risk_nodes:
                    graph.insert_node(n)
                    
                for e in getattr(scenario, 'risk_edges', []):
                    graph.insert_edge(e)
                    
                matches = correlator.evaluate_graph(graph)
                
                # Map nodes to bayesian evidence
                evidence = {
                    "SDNViolation": any(n.event_type == "L2_OBFUSCATION" for n in scenario.risk_nodes),
                    "RestrictedAccess": any(n.event_type == "L3_FILE_RESTRICTED" for n in scenario.risk_nodes),
                    "UnexpectedProcess": any(n.event_type == "L3_PROCESS_CREATE" for n in scenario.risk_nodes),
                    "NetworkActivity": any(n.event_type == "L3_NETWORK" for n in scenario.risk_nodes),
                    "Ptrace": any(n.event_type == "L3_PTRACE" for n in scenario.risk_nodes),
                    "BehavioralDivergence": any(n.event_type == "L4_DIVERGENCE_HIGH" for n in scenario.risk_nodes),
                    "MultiStepChain": len(matches) > 0
                }
                
                # Bayesian risk
                b_result = bayes.evaluate(evidence)
                
                # New Path Analysis
                path_analysis = analyzer.analyze(graph)
                
                # Chain severity
                chain_score = 0.0
                if len(matches) > 0:
                    chain_score = max(
                        [0.3 if m.risk_contribution == "MEDIUM" else 
                         0.7 if m.risk_contribution == "HIGH" else 
                         0.95 for m in matches]
                    )
                    
                # If path analysis found a high risk path, we could optionally boost chain_score
                if path_analysis and path_analysis.get("risk_score", 0.0) > 0.5:
                    chain_score = max(chain_score, 0.8) # Explicitly elevate severity based on verified path
                    
                # Fuzzy governance
                div = 0.9 if evidence["BehavioralDivergence"] else 0.1
                gov_decision = gov.evaluate("test_agent", b_result.attack_probability, div, chain_score, 1.0)
                
                if gov_decision.decision in ["FREEZE", "BLOCK"]:
                    final_decision = type("MockDecision", (), {"decision": DecisionEnum.BLOCK, "source_layers": ["L5"], "risk_score": b_result.attack_probability*100, "confidence": 1.0, "reason_codes": [gov_decision.decision]})()
                    stopping_layer = "L5"
                else:
                    final_decision = type("MockDecision", (), {"decision": DecisionEnum.ALLOW, "source_layers": ["L5"], "risk_score": b_result.attack_probability*100, "confidence": 1.0, "reason_codes": [gov_decision.decision]})()
                
                # Expose specific metrics we need
                result.metadata["b_result"] = b_result.model_dump()
                result.metadata["chain_score"] = chain_score
                result.metadata["gov_decision"] = gov_decision.model_dump()
                result.metadata["graph_stats"] = {"nodes": graph.graph.number_of_nodes(), "edges": graph.graph.number_of_edges()}
                if path_analysis:
                    result.metadata["path_analysis"] = path_analysis
                    
                    # Cross-Session Registry
                    import uuid
                    from common.events.schemas import CrossSessionEvent
                    
                    current_ts = getattr(scenario, 'timestamp_ns', None)
                    if current_ts is None:
                        current_ts = time.time_ns()
                        
                    current_session_id = getattr(scenario, 'session_id', None)
                    if not current_session_id:
                        current_session_id = scenario.scenario_id
                        
                    xs_result = self.cross_session_detector.register_session_fingerprint(
                        session_id=current_session_id,
                        fingerprint=path_analysis["fingerprint"],
                        signature=path_analysis["signature"],
                        path_risk_score=path_analysis["risk_score"],
                        bayesian_probability=b_result.attack_probability,
                        current_time_ns=current_ts
                    )
                    
                    result.metadata["cross_session"] = xs_result
                    
                    # Store as evidence
                    xs_event = CrossSessionEvent(
                        event_id=f"xs-{uuid.uuid4()}",
                        timestamp_ns=time.time_ns(),
                        agent_id="test_agent",
                        session_id=current_session_id,
                        trace_id="t1",
                        current_session_id=xs_result["current_session_id"],
                        matching_session_ids=xs_result["matching_session_ids"],
                        attack_chain_fingerprint=xs_result["fingerprint"],
                        attack_chain_signature=xs_result["signature"],
                        detection_state=xs_result["detection_state"],
                        repeat_count=xs_result["repeat_count"],
                        temporal_window_seconds=self.cross_session_detector.window_seconds,
                        path_risk_score=path_analysis["risk_score"],
                        bayesian_probability=b_result.attack_probability,
                    )
                    
                    self.orchestrator.eces_writer.append_event(xs_event, source_layer="L5_CROSS_SESSION")
                    
                    # Optional escalation
                    if xs_result["detection_state"] in ["REPLAY_ALERT", "COORDINATED_PATTERN"]:
                        chain_score = max(chain_score, 0.95)
                        
                        # We don't overwrite final_decision here, just tracking the metric
                        # In reality, this might trigger a re-eval of the Governance Engine.
                        if final_decision and final_decision.decision != DecisionEnum.BLOCK:
                            final_decision = type("MockDecision", (), {"decision": DecisionEnum.BLOCK, "source_layers": ["L5"], "risk_score": 100, "confidence": 1.0, "reason_codes": [xs_result["detection_state"]]})()
                            stopping_layer = "L5_CROSS_SESSION"

            # Map the outcomes back to the result structure
            if final_decision:
                # Update Layer Outcomes based on what the decision tells us
                layers_visited = final_decision.source_layers
                
                # The orchestrator's SecurityDecision currently just aggregates source layers. 
                # We will mark them as ALLOW or BLOCK based on the final decision logic.
                # If the final decision is BLOCK, the last layer visited is the one that blocked.
                for layer in layers_visited:
                    outcome_decision = "ALLOW"
                    if layer == stopping_layer and final_decision.decision == DecisionEnum.BLOCK:
                        outcome_decision = "BLOCK"
                        
                    outcome = LayerOutcome(
                        decision=outcome_decision,
                        risk_score=final_decision.risk_score,
                        confidence=final_decision.confidence,
                        reason_codes=final_decision.reason_codes
                    )
                    
                    if layer == "L1":
                        result.layer_outcomes.L1 = outcome
                    elif layer == "L2":
                        result.layer_outcomes.L2 = outcome
                    elif layer == "L3":
                        result.layer_outcomes.L3 = outcome
                    elif layer == "L4":
                        result.layer_outcomes.L4 = outcome
                    elif layer == "L5":
                        result.layer_outcomes.L5 = outcome
                
                if final_decision.decision == DecisionEnum.BLOCK:
                    result.attack_blocked = True
                    result.attack_success = False
                else:
                    # If expected to be blocked but wasn't, attack succeeded
                    result.attack_blocked = False
                    result.attack_success = (scenario.expected_security_outcome == DecisionEnum.BLOCK)
                    
            # If telemetry injection was configured, trigger the replay
            if scenario.telemetry_trace and self.orchestrator.l3_collector:
                try:
                    self.orchestrator.l3_collector.run_replay()
                    result.l3_events_processed = len(getattr(self.orchestrator, "l3_events_processed", []))
                    result.l3_anomalies_detected = len(getattr(self.orchestrator, "l3_anomalies", []))
                    
                    if result.l3_events_processed > 0:
                        result.layer_outcomes.L3.decision = "BLOCK" if result.l3_anomalies_detected > 0 else "ALLOW"
                    
                    # Mark L4 and L5 as unavailable for native replay as they are not wired locally
                    result.layer_outcomes.L4.decision = "UNAVAILABLE"
                    result.layer_outcomes.L5.decision = "UNAVAILABLE"
                except Exception as e:
                    result.errors.append(f"Telemetry replay error: {e}")
                    
            result.stopping_layer = stopping_layer

        except Exception as e:
            result.errors.append(str(e))
            result.attack_blocked = True # Failed closed

        end_ns = time.perf_counter_ns()
        result.end_timestamp_ns = end_ns
        result.total_latency_ns = end_ns - start_ns
        
        # Simulated ECES lookup reference based on orchestrator session
        result.evidence_reference = self.orchestrator.session_id

        return result
