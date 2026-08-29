import time
import json
import numpy as np
from l1_gcd.masking import NumpyTokenMasker

def benchmark_vocab(vocab_size, iterations=100):
    # Dummy boolean mask (10% of vocab)
    mask = np.random.rand(vocab_size) > 0.9
    
    masker = NumpyTokenMasker(automaton=None, tokenizer=None)
    
    # Pre-warm
    logits = np.random.randn(vocab_size)
    masker.apply_mask(logits, mask)
    
    times = []
    for _ in range(iterations):
        logits = np.random.randn(vocab_size)
        start = time.perf_counter()
        masked = masker.apply_mask(logits, mask)
        end = time.perf_counter()
        times.append((end - start) * 1000) # milliseconds
        
    return {
        "mean_ms": float(np.mean(times)),
        "median_ms": float(np.median(times)),
        "p50_ms": float(np.percentile(times, 50)),
        "p95_ms": float(np.percentile(times, 95)),
        "p99_ms": float(np.percentile(times, 99))
    }

results = {}
for size in [1000, 8000, 32000, 64000, 128000]:
    res = benchmark_vocab(size)
    results[str(size)] = res

with open("reports/validation/l1-performance.json", "w") as f:
    json.dump(results, f, indent=2)

print("L1 Benchmark saved.")
