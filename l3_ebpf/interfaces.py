from abc import ABC, abstractmethod
from common.events.schemas import SyscallEvent
from typing import List

class EBPFProbeManager(ABC):
    @abstractmethod
    def load_probes(self):
        pass

    @abstractmethod
    def attach_probes(self):
        pass

class EBPFEventReader(ABC):
    @abstractmethod
    def read_events(self) -> List[SyscallEvent]:
        pass

class SyscallTelemetryNormalizer(ABC):
    @abstractmethod
    def normalize(self, raw_telemetry: dict) -> SyscallEvent:
        pass

class KernelEnforcementManager(ABC):
    @abstractmethod
    def enforce_sigstop(self, pid: int):
        pass
