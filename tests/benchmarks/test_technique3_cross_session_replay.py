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
