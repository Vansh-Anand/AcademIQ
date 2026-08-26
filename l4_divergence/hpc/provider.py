import time
import os
import uuid
from typing import Optional
from common.events.schemas import HardwarePerformanceEvent

class HardwareTelemetryProvider:
    """Base class for HPC telemetry."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    def read_counters(self) -> HardwarePerformanceEvent:
        raise NotImplementedError

class NullHPCProvider(HardwareTelemetryProvider):
    """Fallback provider when HPC is completely disabled."""
    def read_counters(self) -> HardwarePerformanceEvent:
        return HardwarePerformanceEvent(
            event_id=f"evt-{uuid.uuid4()}",
            layer="L4",
            trace_id="hpc-telemetry",
            agent_id=self.agent_id,
            timestamp_ns=time.time_ns(),
            simulation=True
        )

class SimulatedHPCProvider(HardwareTelemetryProvider):
    """Provides synthetic microarchitectural behavior for development on Windows."""
    def __init__(self, agent_id: str, is_anomalous: bool = False):
        super().__init__(agent_id)
        self.is_anomalous = is_anomalous
        self.base_cycles = 1_000_000
        
    def read_counters(self) -> HardwarePerformanceEvent:
        import random
        cycles = int(self.base_cycles * random.uniform(0.9, 1.1))
        
        if self.is_anomalous:
            # Anomalous mimicry might cause higher IPC or cache misses
            instructions = int(cycles * random.uniform(2.5, 3.5))
            cache_misses = int(cycles * random.uniform(0.05, 0.1))
        else:
            instructions = int(cycles * random.uniform(0.8, 1.2))
            cache_misses = int(cycles * random.uniform(0.001, 0.005))
            
        ipc = instructions / cycles if cycles > 0 else 0.0
        
        return HardwarePerformanceEvent(
            event_id=f"evt-{uuid.uuid4()}",
            layer="L4",
            trace_id="hpc-telemetry",
            agent_id=self.agent_id,
            timestamp_ns=time.time_ns(),
            simulation=True,
            cycles=cycles,
            instructions=instructions,
            ipc=ipc,
            cache_references=int(cycles * 0.1),
            cache_misses=cache_misses,
            branch_instructions=int(instructions * 0.2),
            branch_misses=int(instructions * 0.01)
        )

class LinuxPerfEventProvider(HardwareTelemetryProvider):
    """Native Linux provider using perf_event_open."""
    def __init__(self, agent_id: str, pid: int):
        super().__init__(agent_id)
        self.pid = pid
        if os.name == 'nt':
            raise RuntimeError("LinuxPerfEventProvider cannot be initialized on Windows. Use SimulatedHPCProvider.")
        
        # In a complete implementation, this would open fds via ctypes/perf_event_open syscall.
        self._fd_cycles = -1
        
    def read_counters(self) -> HardwarePerformanceEvent:
        # Stub for the native implementation
        return HardwarePerformanceEvent(
            event_id=f"evt-{uuid.uuid4()}",
            layer="L4",
            trace_id="hpc-telemetry",
            agent_id=self.agent_id,
            timestamp_ns=time.time_ns(),
            simulation=False,
            cycles=None # Indicates unavailable counters
        )
