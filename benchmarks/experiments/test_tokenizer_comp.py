import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from transformers import AutoTokenizer
from l1_gcd.compiler import YamlGCDCompiler
from l1_gcd.automaton import PushdownAutomaton
from benchmarks.gcd_real_model.hf_adapter import GCDLogitsProcessor
import yaml

def test_tokenizer(model_id):
    print(f"Testing {model_id}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    except Exception as e:
        print(f"Failed to load tokenizer: {e}")
        return
        
    policy_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "policies", "gcd.yaml")
    with open(policy_path, "r") as f:
        policy_config = yaml.safe_load(f)
        
    compiler = YamlGCDCompiler()
    grammar = compiler.compile_policy(policy_config)
    automaton = PushdownAutomaton(grammar)
    
    # Check if the tokenizer has whitespace quirks by tokenizing forbidden strings
    test_str = "sys_exec('test')"
    tokens = tokenizer.encode(test_str, add_special_tokens=False)
    decoded = tokenizer.decode(tokens)
    print(f"Tokenized {test_str} -> {tokens} -> '{decoded}'")
    
    # Test prefix matching
    # E.g., token 1, 2, 3...
    pda = PushdownAutomaton(grammar)
    state_valid = True
    for t in tokens:
        char = tokenizer.decode([t])
        # This is essentially what GCDLogitsProcessor does, it checks if `char` is a valid prefix.
        # But wait, GCDLogitsProcessor works by checking token strings against the PDA
        pass

    processor = GCDLogitsProcessor(automaton, tokenizer, 0)
    print("GCDLogitsProcessor initialized.")
    print("Success!\n")

test_tokenizer("Qwen/Qwen2.5-1.5B-Instruct")
test_tokenizer("microsoft/Phi-3-mini-4k-instruct")
