import numpy as np
from typing import Tuple, List, Optional
from .interfaces import LLMDecoderAdapter
from .tokenizer import TokenizerAdapter
from .automaton import PushdownAutomaton, AutomatonConfiguration
from .masking import NumpyTokenMasker

class DeterministicDecoderAdapter(LLMDecoderAdapter):
    """
    A model-agnostic deterministic decoder for exact-value security tests.
    It takes pre-defined logits and uses the GCD masking layer before applying softmax.
    """
    def __init__(self, tokenizer: TokenizerAdapter):
        self.tokenizer = tokenizer
        
    def decode_with_constraints(
        self, 
        prompt: str, 
        automaton: PushdownAutomaton,
        mock_logits: np.ndarray
    ) -> Tuple[int, np.ndarray, np.ndarray]:
        """
        A single deterministic step simulation.
        Returns: (selected_token_id, raw_probabilities, masked_probabilities)
        """
        config = automaton.initial_config
        masker = NumpyTokenMasker(automaton, self.tokenizer)
        
        # 1. Compute Mask
        mask = masker.compute_legal_token_mask(config)
        
        # 2. Mask Logits
        masked_logits = masker.apply_mask(mock_logits, mask)
        
        # 3. Softmax
        # For raw probs (what would happen without GCD)
        raw_probs = self._softmax(mock_logits)
        
        # For masked probs (what actually happens)
        masked_probs = self._softmax(masked_logits)
        
        # 4. Sampling (Greedy for this deterministic test)
        selected_token_id = int(np.argmax(masked_probs))
        
        return selected_token_id, raw_probs, masked_probs

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        # Subtract max for numerical stability, ignoring -inf
        safe_max = np.max(x[x != -np.inf]) if np.any(x != -np.inf) else 0
        e_x = np.exp(x - safe_max)
        sum_e_x = np.sum(e_x)
        if sum_e_x == 0:
            return np.zeros_like(x)
        return e_x / sum_e_x

class OllamaAdapter:
    """
    Adapter for Ollama. 
    As instructed, Ollama does NOT support pre-softmax logit masking out of the box.
    """
    supports_pre_softmax_masking = False
    
    def decode_with_constraints(self, *args, **kwargs):
        raise NotImplementedError("Ollama does not support hard pre-softmax GCD masking.")
