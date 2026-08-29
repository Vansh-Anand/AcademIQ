import pytest
import os
import sys
import yaml
import torch
from transformers import AutoTokenizer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from l1_gcd.compiler import YamlGCDCompiler
from l1_gcd.automaton import PushdownAutomaton
from benchmarks.gcd_real_model.hf_adapter import GCDLogitsProcessor

@pytest.fixture
def tokenizer():
    return AutoTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")

@pytest.fixture
def policy_config():
    return {
        "allowed_tools": ["web_search", "read_file"],
        "allowed_shell_commands": []
    }

@pytest.fixture
def gcd_processor(tokenizer, policy_config):
    compiler = YamlGCDCompiler()
    grammar = compiler.compile_policy(policy_config)
    automaton = PushdownAutomaton(grammar)
    return GCDLogitsProcessor(automaton, tokenizer, prompt_len=0)

def test_allowed_tools_generatable(gcd_processor, tokenizer):
    """Verify that an allowed tool call prefix is NOT fully masked."""
    # Simulate generating "web_search("
    prefix_ids = tokenizer("web_search(", add_special_tokens=False, return_tensors="pt")["input_ids"]
    scores = torch.zeros((1, tokenizer.vocab_size))
    
    # Apply logits processor
    gcd_processor.prompt_len = 0
    new_scores = gcd_processor(prefix_ids, scores)
    
    # There should be valid paths remaining (not all -inf)
    assert not torch.all(new_scores == -float('inf'))

def test_forbidden_tools_masked(gcd_processor, tokenizer):
    """Verify that a forbidden tool call prefix IS fully masked."""
    # Simulate generating "sys_exec("
    prefix_ids = tokenizer("sys_exec(", add_special_tokens=False, return_tensors="pt")["input_ids"]
    scores = torch.zeros((1, tokenizer.vocab_size))
    
    # Apply logits processor
    gcd_processor.prompt_len = 0
    new_scores = gcd_processor(prefix_ids, scores)
    
    # All scores should be -inf because sys_exec is not in grammar
    assert torch.all(new_scores == -float('inf'))

def test_deterministic_rejection(gcd_processor, tokenizer):
    """Direct prompt injection attempt simulating sys_exec."""
    # Even if top_k has sys_exec fragments, they should be masked.
    scores = torch.rand((1, tokenizer.vocab_size)) 
    prefix_ids = tokenizer("sys_e", add_special_tokens=False, return_tensors="pt")["input_ids"]
    
    new_scores = gcd_processor(prefix_ids, scores)
    assert torch.all(new_scores == -float('inf'))
