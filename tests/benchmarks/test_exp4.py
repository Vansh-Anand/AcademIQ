import pytest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from benchmarks.experiments.exp4_ptrace_behavior import naive_baseline_evaluate

@pytest.fixture
def trace_path():
    return os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "tests", "fixtures", "telemetry", "exp4_ptrace_attempt.jsonl"
    ))

def test_exp4_baseline_detects_all_ptrace(trace_path):
    """
    Test that the naive baseline detects ptrace, but it does so blindly 
    without scoping, creating false positives.
    """
    total, blocked = naive_baseline_evaluate(trace_path)
    assert total == 6
    assert len(blocked) == 2 # Blocks both scoped and out-of-scope ptrace
    
    cgroups = [e.get("cgroup_id") for e in blocked]
    assert 1000 in cgroups # True Positive
    assert 9999 in cgroups # False Positive

def test_exp4_academiq_correlation():
    """
    Validates that the existing pipeline correlates properly.
    """
    from l3_ebpf.userspace.correlation import ExecutionCorrelationManager
    from common.events.schemas import SyscallEvent
    
    manager = ExecutionCorrelationManager()
    
    # Safe execve
    safe_event = SyscallEvent(
        event_id="evt-1",
        timestamp_ns=1000000000,
        layer="L3",
        trace_id="trc-1",
        event_type="Syscall",
        syscall_name="execve",
        pid=1001,
        cgroup_id=1000,
        executable="/bin/ls",
        monotonic_timestamp_ns=1000000000
    )
    
    # Needs authorized command pending to pass
    from l2_sdn.events import NormalizedCommandEvent
    manager.register_l2_decision(NormalizedCommandEvent(
        event_id="dummy", session_id="dummy", trace_id="dummy",
        original_command_hash="dummy", canonical_command_hash="dummy",
        agent_id="test_agent",
        normalized_command="/bin/ls",
        passes_applied=1,
        policy_result="ALLOW"
    ))
    
    safe_event.agent_id = "test_agent"
    correlated, anomaly = manager.correlate_syscall(safe_event)
    assert correlated is True
    assert anomaly is None
    
    # Suspicious ptrace
    ptrace_event = SyscallEvent(
        event_id="evt-2",
        timestamp_ns=2000000100,
        layer="L3",
        trace_id="trc-1",
        event_type="Syscall",
        syscall_name="ptrace",
        pid=1002,
        cgroup_id=1000,
        executable="/usr/bin/python3",
        monotonic_timestamp_ns=2000000100
    )
    ptrace_event.agent_id = "test_agent"
    
    correlated, anomaly = manager.correlate_syscall(ptrace_event)
    assert correlated is False
    assert anomaly is not None
    assert "ptrace attempt" in anomaly.reason
