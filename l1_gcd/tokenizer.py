from abc import ABC, abstractmethod
from typing import Dict, List

class TokenizerAdapter(ABC):
    @abstractmethod
    def encode(self, text: str) -> List[int]:
        pass

    @abstractmethod
    def decode(self, token_ids: List[int]) -> str:
        pass

    @abstractmethod
    def decode_token(self, token_id: int) -> str:
        pass

    @abstractmethod
    def vocab_size(self) -> int:
        pass

    @abstractmethod
    def all_token_ids(self) -> List[int]:
        pass


class MockTokenizer(TokenizerAdapter):
    """A simple mock tokenizer for unit tests."""
    def __init__(self, vocab: Dict[int, str]):
        self.vocab = vocab
        self.inv_vocab = {v: k for k, v in vocab.items()}

    def encode(self, text: str) -> List[int]:
        # Simple greedy mock implementation - not realistic but fine for isolated tests
        res = []
        # In actual usage mock is usually single-token mapping for tests
        if text in self.inv_vocab:
            return [self.inv_vocab[text]]
        return res

    def decode(self, token_ids: List[int]) -> str:
        return "".join(self.vocab.get(tid, "") for tid in token_ids)

    def decode_token(self, token_id: int) -> str:
        return self.vocab.get(token_id, "")

    def vocab_size(self) -> int:
        return max(self.vocab.keys()) + 1 if self.vocab else 0

    def all_token_ids(self) -> List[int]:
        return list(self.vocab.keys())
