import pytest
from l4_divergence.ece.cusum import CUSUMDriftDetector, DriftState
from l4_divergence.ece.manager import ECEManager
from l4_divergence.ece.policy import BaselineAdmissionPolicy
from common.events.schemas import WindowQuality

@pytest.fixture
def manager():
    mgr = ECEManager(percentile=99.0)
    mgr.initialize([0.4] * 1000)
    mgr.enable_drift_detection(reference_value=0.05, decision_threshold=1.0, min_admitted_samples=5)
    return mgr

@pytest.fixture
def quality():
    return WindowQuality(
        event_count=100, expected_count=100, dropped_events=0,
        ordering_valid=True, timestamp_quality=1.0, hpc_coverage=1.0, quality_score=1.0
    )

def test_cusum_stable(manager, quality):
    """Stable observations do not trigger drift."""
    for _ in range(10):
        assert not manager.process_observation(0.42, True)
    assert manager.drift_detector.state in (DriftState.STABLE, DriftState.OBSERVING)

def test_cusum_attack_outlier(manager, quality):
    """A single anomalous outlier does not trigger recalibration."""
    # Simulate blocked by policy
    assert not manager.process_observation(0.99, False)
    assert manager.drift_detector.state == DriftState.STABLE
    assert manager.drift_detector.rejected_candidates == 1
    assert manager.drift_detector.total_observations == 0

def test_cusum_sustained_drift(manager, quality):
    """Sustained legitimate distribution shift triggers drift."""
    # Inject a sustained mean shift from 0.4 to 0.6
    # 0.6 - 0.4 - 0.05 (k) = 0.15 per observation
    # threshold = 1.0. Needs ~7 observations to trigger drift (7 * 0.15 = 1.05 > 1.0)
    for _ in range(8):
        recal = manager.process_observation(0.6, True)
        assert not recal
        
    assert manager.drift_detector.state in (DriftState.DRIFT_SUSPECTED, DriftState.RECALIBRATION_PENDING)

def test_cusum_recalibration(manager, quality):
    """Successful recalibration changes the ECE threshold."""
    initial_threshold = manager.threshold
    
    # 1. Cause Drift
    for _ in range(8):
        manager.process_observation(0.6, True)
    assert manager.drift_detector.state in (DriftState.DRIFT_SUSPECTED, DriftState.RECALIBRATION_PENDING)
    
    # 2. Complete Recalibration Buffer (min 5)
    recalibrated = False
    for _ in range(5):
        if manager.process_observation(0.6, True):
            recalibrated = True
            break
            
    assert recalibrated
    assert manager.drift_detector.state == DriftState.STABLE
    assert manager.threshold > initial_threshold # threshold should have shifted up

def test_recalibration_does_not_occur_before_minimum(manager, quality):
    """Recalibration does not occur before minimum sample requirements."""
    # Cause Drift
    for _ in range(8):
        manager.process_observation(0.6, True)
        
    # Process only 3 candidate samples (min is 5)
    for _ in range(3):
        assert not manager.process_observation(0.6, True)
        
    assert manager.drift_detector.state == DriftState.RECALIBRATION_PENDING
