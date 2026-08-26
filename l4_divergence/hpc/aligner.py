from typing import List, Dict, Optional
from common.events.schemas import HardwarePerformanceEvent, SyscallEvent

class HPCFeatureVector:
    """Standardized vector representing hardware telemetry over a window."""
    def __init__(self, mean_cycles: float, mean_ipc: float, mean_cache_miss_rate: float,
                 mean_branch_miss_rate: float, available: bool = True):
        self.mean_cycles = mean_cycles
        self.mean_ipc = mean_ipc
        self.mean_cache_miss_rate = mean_cache_miss_rate
        self.mean_branch_miss_rate = mean_branch_miss_rate
        self.available = available
        
    def to_list(self) -> List[float]:
        # Include an availability flag in the vector itself for the neural network
        avail_flag = 1.0 if self.available else 0.0
        return [
            self.mean_cycles, 
            self.mean_ipc, 
            self.mean_cache_miss_rate, 
            self.mean_branch_miss_rate,
            avail_flag
        ]

class HPCWindowAligner:
    """
    Aligns asynchronous HPC telemetry points with a window of SyscallEvents.
    Averaging HPC samples that fall temporally inside the window.
    """
    def align(self, window_events: List[SyscallEvent], hpc_events: List[HardwarePerformanceEvent]) -> HPCFeatureVector:
        if not window_events:
            return HPCFeatureVector(0.0, 0.0, 0.0, 0.0, available=False)
            
        start_ns = window_events[0].timestamp_ns
        end_ns = window_events[-1].timestamp_ns
        
        # Filter HPC events within the window
        relevant = [e for e in hpc_events if start_ns <= e.timestamp_ns <= end_ns]
        
        if not relevant:
            # If no HPC data overlaps, assume unavailable or missing
            return HPCFeatureVector(0.0, 0.0, 0.0, 0.0, available=False)
            
        total_cycles = 0
        total_ipc = 0.0
        total_cm_rate = 0.0
        total_bm_rate = 0.0
        count = 0
        
        for e in relevant:
            if e.cycles is not None:
                total_cycles += e.cycles
                total_ipc += (e.ipc or 0.0)
                if e.cache_references and e.cache_references > 0:
                    total_cm_rate += (e.cache_misses or 0) / e.cache_references
                if e.branch_instructions and e.branch_instructions > 0:
                    total_bm_rate += (e.branch_misses or 0) / e.branch_instructions
                count += 1
                
        if count == 0:
            return HPCFeatureVector(0.0, 0.0, 0.0, 0.0, available=False)
            
        return HPCFeatureVector(
            mean_cycles=total_cycles / count,
            mean_ipc=total_ipc / count,
            mean_cache_miss_rate=total_cm_rate / count,
            mean_branch_miss_rate=total_bm_rate / count,
            available=True
        )
