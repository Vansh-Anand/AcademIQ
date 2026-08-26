import numpy as np
from typing import List, Optional
from .interfaces import TokenMasker
from .tokenizer import TokenizerAdapter
from .automaton import PushdownAutomaton, AutomatonConfiguration

class NumpyTokenMasker(TokenMasker):
    def __init__(self, automaton: PushdownAutomaton, tokenizer: TokenizerAdapter):
        self.automaton = automaton
        self.tokenizer = tokenizer
        
    def compute_legal_token_mask(self, config: AutomatonConfiguration) -> np.ndarray:
        """
        Computes a boolean mask for all tokens in the vocabulary.
        True = legal, False = illegal.
        """
        vocab_size = self.tokenizer.vocab_size()
        mask = np.zeros(vocab_size, dtype=bool)
        
        for token_id in self.tokenizer.all_token_ids():
            token_text = self.tokenizer.decode_token(token_id)
            if self.automaton.is_valid_prefix(token_text, config):
                mask[token_id] = True
                
        return mask
        
    def apply_mask(self, logits: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Applies -inf to illegal logits.
        """
        # Create a copy so we don't mutate the original if it's reused
        masked_logits = np.copy(logits)
        masked_logits[~mask] = -np.inf
        return masked_logits
