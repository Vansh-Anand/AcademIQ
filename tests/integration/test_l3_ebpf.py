import pytest
import os
import time
from l3_ebpf.namespace.scope import AgentScopeManager
from l3_ebpf.userspace.health import TelemetryHealthMonitor
from l3_ebpf.userspace.collector import SimulatedL3Collector
from l3_ebpf.userspace.correlation import ExecutionCorrelationManager
from common.events.schemas import SyscallEvent
from l2_sdn.events import NormalizedCommandEvent

@pytest.fixture
def scope_manager():
    sm = AgentScopeManager()
    sm.register_agent("test_agent_1", 1000, 1234)
    return sm

@pytest.fixture
def correlation_manager():
    return ExecutionCorrelationManager()

@pytest.fixture
def trace_file():
    # Make sure we use the fixture file
    return os.path.join(os.path.dirname(__file__), "..", "fixtures", "telemetry", "execve_trace.jsonl")

def test_l3_correlation_pipeline(scope_manager, correlation_manager, trace_file):
    hm = TelemetryHealthMonitor()
    collector = SimulatedL3Collector(scope_manager, hm, trace_file)
    
    events_received = []
    anomalies_detected = []
    
    def process_event(event: SyscallEvent):
        events_received.append(event)
        correlated, anomaly = correlation_manager.correlate_syscall(event)
        if not correlated:
            anomalies_detected.append(anomaly)
            
    collector.register_callback(process_event)
    
    # 1. Run without prior L2 authorization
    collector.run_replay()
    
    assert len(events_received) == 2
    assert len(anomalies_detected) == 2 # cat and curl both blocked
    assert anomalies_detected[0].reason.startswith("Unexpected execve(/bin/cat)")
    assert anomalies_detected[1].reason.startswith("Unauthorized network activity")
    
    # 2. Add an L2 authorization for cat
    l2_event = NormalizedCommandEvent(
        event_id="test",
        schema_version="1.0",
        session_id="sess",
        trace_id="trc",
        agent_id="test_agent_1",
        timestamp_ns=time.time_ns(),
        original_command_hash="hash",
        canonical_command_hash="hash",
        normalization_passes=[],
        obfuscation_detected=False,
        transformations=[],
        policy_result="ALLOW",
        matched_rule="OK",
        path_identities=[],
        security_decision="ALLOW"
    )
    correlation_manager.register_l2_decision(l2_event)
    
    # Re-run
    events_received.clear()
    anomalies_detected.clear()
    collector.run_replay()
    
    # Execve for cat should now be correlated (allowed), network should still be blocked
    assert len(anomalies_detected) == 1
    assert anomalies_detected[0].reason.startswith("Unauthorized network activity")
