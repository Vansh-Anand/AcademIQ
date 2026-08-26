import pytest
import time
from common.events.schemas import ShellCommandEvent
from common.schemas.security import DecisionEnum
from l2_sdn.interceptor import L2Interceptor

@pytest.fixture
def interceptor():
    # Use the default policy which allows 'cat', 'read_file' but blocks '/etc'
    return L2Interceptor()

def test_l2_allows_safe_command(interceptor):
    event = ShellCommandEvent(
        event_id="test1",
        timestamp_ns=time.time_ns(),
        trace_id="trace1",
        layer="L2",
        raw_command="cat /tmp/safe.txt"
    )
    decision, ast = interceptor.intercept(event)
    # /tmp/safe.txt is not forbidden, cat is allowed
    assert decision.decision == DecisionEnum.ALLOW

def test_l2_blocks_forbidden_directory(interceptor):
    event = ShellCommandEvent(
        event_id="test2",
        timestamp_ns=time.time_ns(),
        trace_id="trace1",
        layer="L2",
        raw_command="cat /etc/passwd"
    )
    decision, ast = interceptor.intercept(event)
    assert decision.decision == DecisionEnum.BLOCK
    assert decision.reason_codes[0] == "SDN_POLICY_VIOLATION"

def test_l2_blocks_adversarial_traversal(interceptor):
    # L1 might allow this structurally, but L2 must block it semantically
    # by normalizing the path before checking.
    event = ShellCommandEvent(
        event_id="test3",
        timestamp_ns=time.time_ns(),
        trace_id="trace1",
        layer="L2",
        raw_command="cat /tmp/../../etc/passwd"
    )
    decision, ast = interceptor.intercept(event)
    assert decision.decision == DecisionEnum.BLOCK

def test_l2_blocks_adversarial_quoting(interceptor):
    # Obfuscating the path with quotes
    event = ShellCommandEvent(
        event_id="test4",
        timestamp_ns=time.time_ns(),
        trace_id="trace1",
        layer="L2",
        raw_command="cat \"/et\"c/passwd"
    )
    decision, ast = interceptor.intercept(event)
    assert decision.decision == DecisionEnum.BLOCK

def test_l2_blocks_forbidden_argument(interceptor):
    # --force is forbidden
    event = ShellCommandEvent(
        event_id="test5",
        timestamp_ns=time.time_ns(),
        trace_id="trace1",
        layer="L2",
        raw_command="cat --force /tmp/file.txt"
    )
    decision, ast = interceptor.intercept(event)
    assert decision.decision == DecisionEnum.BLOCK
