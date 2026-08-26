import pytest
from common.events.schemas import ToolInvocationEvent
from common.schemas.security import SecurityDecision, DecisionEnum
import time

def test_tool_invocation_event_creation():
    event = ToolInvocationEvent(
        event_id="test-123",
        timestamp_ns=time.time_ns(),
        layer="L1",
        trace_id="trace-123",
        tool_name="test_tool",
        arguments={"arg1": "val1"}
    )
    assert event.event_type == "ToolInvocation"
    assert event.tool_name == "test_tool"
    assert event.layer == "L1"

def test_security_decision_validation():
    decision = SecurityDecision(
        decision=DecisionEnum.ALLOW,
        reason_codes=["TEST"],
        risk_score=5.0,
        confidence=0.9,
        source_layers=["L1"],
        related_event_ids=["evt-1"],
        timestamp_ns=time.time_ns()
    )
    assert decision.decision == DecisionEnum.ALLOW
    assert decision.risk_score == 5.0
