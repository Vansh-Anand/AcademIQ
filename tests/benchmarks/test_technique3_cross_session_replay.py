import pytest
import time
from common.events.schemas import DetectionState
from l5_riskchain.correlation.cross_session import CrossSessionReplayDetector

@pytest.fixture
def detector():
    # Setup detector with 1 hr window, repeat threshold 2, coordinated 3
    return CrossSessionReplayDetector(window_seconds=3600, repeat_threshold=2, coordinated_threshold=3, risk_threshold=0.5)

def test_first_observation_is_new_pattern(detector):
    result = detector.register_session_fingerprint(
        session_id="session_1",
        fingerprint="hash_A",
        signature="A->B",
        path_risk_score=0.8,
        bayesian_probability=0.7
    )
    assert result["detection_state"] == DetectionState.NEW_PATTERN.value
    assert result["repeat_count"] == 1
    assert result["is_high_risk"] is True

def test_same_fingerprint_detected_as_replay(detector):
    detector.register_session_fingerprint("s1", "hash_A", "A->B", 0.8, 0.7)
    
    result = detector.register_session_fingerprint(
        session_id="s2",
        fingerprint="hash_A",
        signature="A->B",
        path_risk_score=0.8,
        bayesian_probability=0.7
    )
    assert result["detection_state"] == DetectionState.REPLAY_ALERT.value
    assert result["repeat_count"] == 2
    assert "s1" in result["matching_session_ids"]

def test_benign_workflow_not_alerted(detector):
    # Low risk path
    detector.register_session_fingerprint("s1", "hash_B", "X->Y", 0.2, 0.2)
    
    result = detector.register_session_fingerprint(
        session_id="s2",
        fingerprint="hash_B",
        signature="X->Y",
        path_risk_score=0.2,
        bayesian_probability=0.2
    )
    # Should be legitimate repeat, not replay alert
    assert result["detection_state"] == DetectionState.LEGITIMATE_REPEAT.value
    assert result["repeat_count"] == 2

def test_coordinated_attack_threshold(detector):
    ts = time.time_ns()
    # 3 sessions in close proximity
    detector.register_session_fingerprint("s1", "hash_C", "A->C", 0.9, 0.9, ts)
    detector.register_session_fingerprint("s2", "hash_C", "A->C", 0.9, 0.9, ts + 1000)
    
    result = detector.register_session_fingerprint("s3", "hash_C", "A->C", 0.9, 0.9, ts + 2000)
    
    assert result["detection_state"] == DetectionState.COORDINATED_PATTERN.value
    assert result["repeat_count"] == 3
    
def test_outside_temporal_window_not_coordinated(detector):
    ts = time.time_ns()
    # 3 sessions, but one is outside the 1 hour window (3600 seconds)
    detector.register_session_fingerprint("s1", "hash_D", "A->D", 0.9, 0.9, ts)
    detector.register_session_fingerprint("s2", "hash_D", "A->D", 0.9, 0.9, ts + 1000)
    
    ts_outside = ts + (7200 * 1_000_000_000) # 2 hours later
    result = detector.register_session_fingerprint("s3", "hash_D", "A->D", 0.9, 0.9, ts_outside)
    
    # It hits repeat_count 3, but because they are outside the window, 
    # it downgrades from COORDINATED to REPLAY_ALERT
    assert result["detection_state"] == DetectionState.REPLAY_ALERT.value
    assert result["repeat_count"] == 3

@pytest.fixture
def writer(tmp_path):
    from l6_eces.chain.writer import EvidenceChainWriter
    from l6_eces.chain.store import JsonlEvidenceStore
    from l6_eces.crypto.hasher import HashProvider
    from l6_eces.crypto.signer import SoftwareSigner
    
    store = JsonlEvidenceStore(directory=str(tmp_path / "evidence"))
    hasher = HashProvider()
    signer = SoftwareSigner()
    signer.generate_key()
    
    return EvidenceChainWriter(store, hasher, signer)

def test_a_event_construction(writer):
    from common.events.schemas import CrossSessionEvent
    import uuid
    import time
    
    xs_event = CrossSessionEvent(
        event_id=f"xs-{uuid.uuid4()}",
        timestamp_ns=time.time_ns(),
        agent_id="test_agent",
        session_id="s1",
        trace_id="t1",
        current_session_id="s2",
        matching_session_ids=["s1"],
        attack_chain_fingerprint="hash_A",
        attack_chain_signature="A->B",
        detection_state="REPLAY_ALERT",
        repeat_count=2,
        temporal_window_seconds=3600,
        path_risk_score=0.8,
        bayesian_probability=0.7
    )
    
    # Assert layer is populated correctly by default
    assert xs_event.layer == "L5_CROSS_SESSION"
    
    # Assert serialization succeeds
    entry = writer.append_event(xs_event, source_layer="L5_CROSS_SESSION")
    
    assert entry.event_id == xs_event.event_id
    assert entry.source_layer == "L5_CROSS_SESSION"
    
def test_b_exact_replay_scenario(detector, writer):
    from common.events.schemas import CrossSessionEvent
    import uuid
    import time
    
    detector.register_session_fingerprint("s1", "hash_X", "A->B", 0.9, 0.9)
    result = detector.register_session_fingerprint("s2", "hash_X", "A->B", 0.9, 0.9)
    
    assert result["detection_state"] == DetectionState.REPLAY_ALERT.value
    
    xs_event = CrossSessionEvent(
        event_id=f"xs-{uuid.uuid4()}",
        timestamp_ns=time.time_ns(),
        agent_id="test_agent",
        session_id="s2",
        trace_id="t2",
        current_session_id=result["current_session_id"],
        matching_session_ids=result["matching_session_ids"],
        attack_chain_fingerprint=result["fingerprint"],
        attack_chain_signature=result["signature"],
        detection_state=result["detection_state"],
        repeat_count=result["repeat_count"],
        temporal_window_seconds=3600,
        path_risk_score=0.9,
        bayesian_probability=0.9
    )
    assert xs_event.layer == "L5_CROSS_SESSION"
    
    entry = writer.append_event(xs_event, source_layer=xs_event.layer)
    assert entry.signature is not None

def test_c_coordinated_attack_scenario(detector, writer):
    from common.events.schemas import CrossSessionEvent
    import uuid
    import time
    
    ts = time.time_ns()
    detector.register_session_fingerprint("s1", "hash_C", "A->C", 0.9, 0.9, ts)
    detector.register_session_fingerprint("s2", "hash_C", "A->C", 0.9, 0.9, ts + 1000)
    result = detector.register_session_fingerprint("s3", "hash_C", "A->C", 0.9, 0.9, ts + 2000)
    
    assert result["detection_state"] == DetectionState.COORDINATED_PATTERN.value
    
    xs_event = CrossSessionEvent(
        event_id=f"xs-{uuid.uuid4()}",
        timestamp_ns=time.time_ns(),
        agent_id="test_agent",
        session_id="s3",
        trace_id="t3",
        current_session_id=result["current_session_id"],
        matching_session_ids=result["matching_session_ids"],
        attack_chain_fingerprint=result["fingerprint"],
        attack_chain_signature=result["signature"],
        detection_state=result["detection_state"],
        repeat_count=result["repeat_count"],
        temporal_window_seconds=3600,
        path_risk_score=0.9,
        bayesian_probability=0.9
    )
    assert xs_event.layer == "L5_CROSS_SESSION"
    
    entry = writer.append_event(xs_event, source_layer=xs_event.layer)
    assert entry.source_layer == "L5_CROSS_SESSION"

def test_d_legitimate_repeat(detector):
    from common.events.schemas import CrossSessionEvent
    import uuid
    import time
    
    detector.register_session_fingerprint("s1", "hash_Y", "X->Y", 0.2, 0.2)
    result = detector.register_session_fingerprint("s2", "hash_Y", "X->Y", 0.2, 0.2)
    
    assert result["detection_state"] == DetectionState.LEGITIMATE_REPEAT.value
    
    # Should still serialize without error
    xs_event = CrossSessionEvent(
        event_id=f"xs-{uuid.uuid4()}",
        timestamp_ns=time.time_ns(),
        agent_id="test_agent",
        session_id="s2",
        trace_id="t2",
        current_session_id=result["current_session_id"],
        matching_session_ids=result["matching_session_ids"],
        attack_chain_fingerprint=result["fingerprint"],
        attack_chain_signature=result["signature"],
        detection_state=result["detection_state"],
        repeat_count=result["repeat_count"],
        temporal_window_seconds=3600,
        path_risk_score=0.2,
        bayesian_probability=0.2
    )
    assert xs_event.layer == "L5_CROSS_SESSION"
