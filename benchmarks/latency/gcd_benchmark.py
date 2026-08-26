import time
import numpy as np
from l1_gcd.tokenizer import MockTokenizer
from l1_gcd.grammar import Grammar, StartSymbol, Terminal, NonTerminal, ProductionRule
from l1_gcd.automaton import PushdownAutomaton
from l1_gcd.adapters import DeterministicDecoderAdapter

def run_benchmark():
    print("--- L1 GCD Latency Benchmark ---")
    print("WARNING: DEVELOPMENT ENVIRONMENT (Windows Python)")
    
    # Setup mock vocab of 32000 (standard for LLaMA scale)
    vocab_size = 32000
    vocab = {i: f"token_{i}" for i in range(vocab_size)}
    vocab[0] = "read_file"
    tokenizer = MockTokenizer(vocab)
    
    start = StartSymbol("S")
    tool_call = NonTerminal("TOOL")
    rules = [
        ProductionRule(start, [tool_call]),
        ProductionRule(tool_call, [Terminal("read_file")])
    ]
    grammar = Grammar(start, rules)
    pda = PushdownAutomaton(grammar)
    
    adapter = DeterministicDecoderAdapter(tokenizer)
    
    iterations = 100
    times = []
    
    for _ in range(iterations):
        mock_logits = np.random.randn(vocab_size)
        
        t0 = time.perf_counter()
        adapter.decode_with_constraints("prompt", pda, mock_logits)
        t1 = time.perf_counter()
        
        times.append((t1 - t0) * 1000) # milliseconds
        
    times = np.array(times)
    print(f"Mean Latency:   {np.mean(times):.3f} ms")
    print(f"Median Latency: {np.median(times):.3f} ms")
    print(f"p95 Latency:    {np.percentile(times, 95):.3f} ms")
    print(f"p99 Latency:    {np.percentile(times, 99):.3f} ms")
    
    target = 0.8
    if np.mean(times) < target:
        print(f"Result: SUCCESS (Achieved < {target} ms)")
    else:
        print(f"Result: TARGET NOT YET ACHIEVED (Mean > {target} ms on this dev host)")

if __name__ == "__main__":
    run_benchmark()
