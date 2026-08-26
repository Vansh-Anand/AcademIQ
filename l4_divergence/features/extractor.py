import math
from typing import List, Dict, Optional
from common.events.schemas import SyscallEvent, HardwarePerformanceEvent
from l4_divergence.hpc.aligner import HPCWindowAligner
from l4_divergence.features.vocabulary import SyscallVocabulary

class BehaviorFeatureVector:
    """Container for the extracted features."""
    def __init__(self):
        self.sequence_features: List[int] = []  # Syscall category indices
        self.timing_features: List[float] = []  # log1p delta timings
        self.transition_features: List[float] = [] # Flattened transition matrix or frequencies
        self.process_features: List[float] = [] # Pids / process counts
        self.hpc_features: List[float] = [] # From HPCFeatureVector
        self.hpc_available: bool = False
        
    def to_flat_numeric(self) -> List[float]:
        # Combines the non-sequence numeric features for Isolation Forest
        return self.timing_features + self.transition_features + self.process_features + self.hpc_features

class BehaviorFeatureExtractor:
    """Extracts ML features from a behavioral window."""
    def __init__(self, vocabulary: SyscallVocabulary, hpc_aligner: HPCWindowAligner):
        self.vocab = vocabulary
        self.hpc_aligner = hpc_aligner
        
    def extract(self, window_events: List[SyscallEvent], hpc_events: List[HardwarePerformanceEvent]) -> BehaviorFeatureVector:
        vec = BehaviorFeatureVector()
        
        # 1. Sequence and Timings
        prev_time = None
        for i, event in enumerate(window_events):
            idx = self.vocab.encode(event.syscall_name)
            vec.sequence_features.append(idx)
            
            if prev_time is None:
                vec.timing_features.append(0.0)
            else:
                delta_ns = max(0, event.timestamp_ns - prev_time)
                # log1p to compress huge timing disparities safely
                vec.timing_features.append(math.log1p(delta_ns))
            prev_time = event.timestamp_ns
            
        # 2. Transition Matrix (simplified to global frequencies for numeric)
        freqs = [0.0] * self.vocab.size()
        if len(window_events) > 0:
            for idx in vec.sequence_features:
                freqs[idx] += 1.0
            freqs = [f / len(window_events) for f in freqs]
        vec.transition_features = freqs
        
        # 3. Process Identity Transitions
        unique_pids = len(set(e.pid for e in window_events))
        vec.process_features = [float(unique_pids)]
        
        # 4. HPC Features
        hpc_vec = self.hpc_aligner.align(window_events, hpc_events)
        vec.hpc_features = hpc_vec.to_list()
        vec.hpc_available = hpc_vec.available
        
        return vec
