from abc import ABC, abstractmethod
from typing import Optional

class TEEProvider(ABC):
    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def get_attestation(self) -> Optional[str]:
        pass

    @abstractmethod
    def protect_memory(self):
        pass

    @abstractmethod
    def execute_protected(self, func, *args, **kwargs):
        pass

    @abstractmethod
    def seal_state(self, data: bytes) -> bytes:
        pass

    @abstractmethod
    def unseal_state(self, sealed_data: bytes) -> bytes:
        pass

class NullTEEProvider(TEEProvider):
    def initialize(self):
        pass
    def is_available(self) -> bool:
        return False
    def get_attestation(self) -> Optional[str]:
        return None
    def protect_memory(self):
        pass
    def execute_protected(self, func, *args, **kwargs):
        return func(*args, **kwargs)
    def seal_state(self, data: bytes) -> bytes:
        return data
    def unseal_state(self, sealed_data: bytes) -> bytes:
        return sealed_data

class SimulationTEEProvider(TEEProvider):
    def initialize(self):
        print("[SimulationTEE] Initialized.")
    def is_available(self) -> bool:
        return True
    def get_attestation(self) -> Optional[str]:
        return "MOCK_ATTESTATION_QUOTE_SIMULATION"
    def protect_memory(self):
        pass
    def execute_protected(self, func, *args, **kwargs):
        return func(*args, **kwargs)
    def seal_state(self, data: bytes) -> bytes:
        return b"SIM_SEALED_" + data
    def unseal_state(self, sealed_data: bytes) -> bytes:
        return sealed_data.replace(b"SIM_SEALED_", b"")
