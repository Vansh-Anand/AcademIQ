from abc import ABC, abstractmethod
from typing import Optional
from common.events.schemas import HardwarePerformanceEvent
import time

class HardwareTelemetryProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def sample(self) -> HardwarePerformanceEvent:
        pass

    @abstractmethod
    def stop(self):
        pass

class NullHPCProvider(HardwareTelemetryProvider):
    def is_available(self) -> bool:
        return False
    def start(self):
        pass
    def sample(self) -> HardwarePerformanceEvent:
        return HardwarePerformanceEvent(
            event_id="null-hpc",
            timestamp_ns=time.time_ns(),
            layer="H3",
            trace_id="null",
            simulation=False
        )
    def stop(self):
        pass

class SimulationHPCProvider(HardwareTelemetryProvider):
    def is_available(self) -> bool:
        return True
    def start(self):
        pass
    def sample(self) -> HardwarePerformanceEvent:
        return HardwarePerformanceEvent(
            event_id="sim-hpc-123",
            timestamp_ns=time.time_ns(),
            layer="H3",
            trace_id="sim-trace",
            simulation=True,
            cycles=1500000,
            instructions=3000000,
            ipc=2.0,
            cache_references=50000,
            cache_misses=1200
        )
    def stop(self):
        pass
