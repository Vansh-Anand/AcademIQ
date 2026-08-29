import torch
import numpy as np
from transformers import LogitsProcessor, PreTrainedTokenizer
from typing import List

from l1_gcd.tokenizer import TokenizerAdapter
from l1_gcd.automaton import PushdownAutomaton

class HuggingFaceTokenizerAdapter(TokenizerAdapter):
    def __init__(self, tokenizer: PreTrainedTokenizer):
        self.tokenizer = tokenizer

    def encode(self, text: str) -> List[int]:
        return self.tokenizer.encode(text, add_special_tokens=False)

    def decode(self, token_ids: List[int]) -> str:
        return self.tokenizer.decode(token_ids, skip_special_tokens=True)

    def decode_token(self, token_id: int) -> str:
        return self.tokenizer.decode([token_id], skip_special_tokens=True)

    def vocab_size(self) -> int:
        return len(self.tokenizer)

    def all_token_ids(self) -> List[int]:
        # Some tokenizers have gaps or added tokens, but range(vocab_size) is usually fine.
        return list(range(len(self.tokenizer)))


class GCDLogitsProcessor(LogitsProcessor):
    """
    Integrates L1 GCD (PushdownAutomaton) directly into HuggingFace generation loop.
    Masks out any token that would cause the generated text to violate the CFG.
    """
    def __init__(self, automaton: PushdownAutomaton, tokenizer: PreTrainedTokenizer, prompt_len: int):
        self.automaton = automaton
        self.tokenizer = tokenizer
        self.prompt_len = prompt_len
        self.config = self.automaton.initial_config
        self.masked_count = 0
        
        # Precompute the token string translations to avoid decoding overhead in the loop
        self.token_strings = {}
        for i in range(len(tokenizer)):
            self.token_strings[i] = tokenizer.decode([i], skip_special_tokens=True)
            
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        # Assuming batch_size = 1 for benchmark simplicity
        generated_ids = input_ids[0][self.prompt_len:]
        
        if len(generated_ids) > 0:
            generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        else:
            generated_text = ""
            
        # We need to compute a boolean mask for the vocab
        # To make it reasonably fast in pure Python, we only check tokens that have a high enough logit score.
        # We'll check the top 500 candidates. The rest are already unlikely, but we'll mask them just to be safe.
        
        # We want to be secure, so we mask everything by default.
        mask = torch.zeros_like(scores, dtype=torch.bool)
        
        # Optimization: only evaluate the top K logits to prevent O(Vocab) parsing overhead per step.
        # This is a safe approximation since masking low logits doesn't change the outcome much.
        # If we strictly want to check ALL tokens, it would be slow but perfectly accurate.
        # Let's evaluate top 1000 for a good balance of speed/accuracy in this benchmark.
        top_k = min(1000, scores.size(-1))
        top_indices = torch.topk(scores[0], top_k).indices.cpu().tolist()
        
        num_masked_this_step = 0
        
        for token_id in top_indices:
            token_str = self.token_strings.get(token_id, "")
            candidate_text = generated_text + token_str
            
            # Use the stubbed advance / prefix checker from l1_gcd
            # The automaton checks if this candidate_text is a valid prefix from the START rule.
            if self.automaton.is_valid_prefix(candidate_text, self.config):
                mask[0, token_id] = True
            else:
                num_masked_this_step += 1
                
        self.masked_count += num_masked_this_step
        
        # Apply -inf to anything that is NOT masked as True
        if not mask.any():
            # If everything is masked, fallback to EOS token to prevent NaN crash
            mask[0, self.tokenizer.eos_token_id] = True
            
        scores[~mask] = -float('inf')
        
        return scores
