import pytest
import numpy as np
from common.events.schemas import SyscallEvent, WindowQuality
from l4_divergence.features.vocabulary import SyscallVocabulary
from l4_divergence.hpc.aligner import HPCWindowAligner
from l4_divergence.features.extractor import BehaviorFeatureExtractor
from l4_divergence.features.normalizer import FeatureNormalizer
from l4_divergence.dataset.loader import DatasetBuilder
from l4_divergence.siamese.model import SiameseRecurrentAutoencoder
from l4_divergence.isolation_forest.detector import IsolationForestDetector
from l4_divergence.ensemble.divergence import DivergenceEnsemble
from l4_divergence.ece.manager import ECEManager
from l4_divergence.ece.policy import BaselineAdmissionPolicy

@pytest.fixture
def l4_components():
    vocab = SyscallVocabulary()
    aligner = HPCWindowAligner()
    extractor = BehaviorFeatureExtractor(vocab, aligner)
    normalizer = FeatureNormalizer()
    return vocab, aligner, extractor, normalizer

def test_l4_telemetry_fusion(l4_components):
    vocab, aligner, extractor, normalizer = l4_components
    builder = DatasetBuilder("agent_test")
    
    # Generate 50 legit, 10 attack
    dataset = builder.build_dataset(num_legit=50, num_attack=10, window_size=64)
    legit_windows = dataset["legitimate"]
    attack_windows = dataset["attack"]
    
    # Extract features
    legit_features = [extractor.extract(seq, hpc) for seq, hpc in legit_windows]
    numeric_flat = [f.to_flat_numeric() for f in legit_features]
    
    normalizer.fit(numeric_flat)
    normalized = np.array([normalizer.transform(f) for f in numeric_flat])
    
    # Train Isolation Forest
    iso = IsolationForestDetector()
    iso.fit(normalized)
    
    # Verify attacks score higher
    attack_features = [extractor.extract(seq, hpc) for seq, hpc in attack_windows]
    attack_flat = np.array([normalizer.transform(f.to_flat_numeric()) for f in attack_features])
    
    legit_scores = iso.score(normalized)
    attack_scores = iso.score(attack_flat)
    
    # On average, attacks should be more anomalous
    assert np.mean(attack_scores) > np.mean(legit_scores)

def test_ece_poisoning_defense():
    manager = ECEManager(percentile=99.0)
    # Initialize baseline
    legit_scores = [0.1, 0.12, 0.15, 0.09, 0.11]
    manager.initialize(legit_scores)
    
    policy = BaselineAdmissionPolicy(current_threshold=manager.threshold, margin=0.2)
    quality = WindowQuality(event_count=256, expected_count=256, dropped_events=0, ordering_valid=True, timestamp_quality=1.0, hpc_coverage=1.0, quality_score=1.0)
    
    # Should accept normal
    assert policy.is_admissible(0.13, quality) is True
    
    # Should reject obvious attack
    assert policy.is_admissible(0.85, quality) is False
    
    # Should reject low quality even if score is low
    poor_quality = WindowQuality(event_count=200, expected_count=256, dropped_events=56, ordering_valid=True, timestamp_quality=0.5, hpc_coverage=0.0, quality_score=0.4)
    assert policy.is_admissible(0.12, poor_quality) is False
