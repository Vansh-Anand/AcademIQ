from abc import ABC, abstractmethod

class GCDPolicyCompiler(ABC):
    @abstractmethod
    def compile_policy(self, policy_config: dict) -> any:
        pass

class GrammarAutomaton(ABC):
    @abstractmethod
    def is_valid_token(self, token_id: int) -> bool:
        pass

class TokenMasker(ABC):
    @abstractmethod
    def apply_mask(self, logits: list[float], valid_tokens: list[int]) -> list[float]:
        pass

class LLMDecoderAdapter(ABC):
    @abstractmethod
    def decode_with_constraints(self, prompt: str, automaton: GrammarAutomaton) -> str:
        pass
