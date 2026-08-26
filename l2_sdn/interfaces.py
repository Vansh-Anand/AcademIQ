from abc import ABC, abstractmethod
from common.events.schemas import ShellCommandEvent, NormalizedCommandEvent
from typing import List

class ShellInterceptor(ABC):
    @abstractmethod
    def intercept(self, event: ShellCommandEvent) -> bool:
        pass

class CommandParser(ABC):
    @abstractmethod
    def parse(self, command: str) -> dict:
        pass

class NormalizationPass(ABC):
    @abstractmethod
    def apply(self, ast: dict) -> dict:
        pass

class CommandCanonicalizer(ABC):
    @abstractmethod
    def canonicalize(self, command: str) -> str:
        pass

class CommandPolicyMatcher(ABC):
    @abstractmethod
    def match(self, normalized_event: NormalizedCommandEvent) -> bool:
        pass
