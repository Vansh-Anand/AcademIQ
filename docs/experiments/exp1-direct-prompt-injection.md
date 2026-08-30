# EXP-1: Direct Prompt Injection / Forbidden Tool Invocation

## Threat Model
In an agentic LLM environment, an attacker may inject instructions into untrusted inputs (e.g. web pages, incoming emails) that hijack the model's generated sequence. If the model parses and complies with these instructions, it might attempt to execute a forbidden tool invocation on the underlying system.

## Objective
To demonstrate that the AcademIQ pipeline defends against forbidden tool invocation via two distinct layers:
1. **Model-Level Prevention (L1 GCD)**: Preemptively preventing the model from generating forbidden tool tokens through CFG-based logits masking.
2. **Pipeline-Level Fallback**: Blocking forbidden tool execution explicitly in the orchestrator if the generation protections are bypassed.

*Note: This methodology was strengthened in Phase A1 from a small N=5 pilot into a statistically robust benchmark with N=120 attack attempts across 10 semantic categories.*

## Attack Setup
**Target Tool**: `sys_exec`, `delete_file`, `write_file`, `reboot_system`
**Constraint**: The existing production security policy `config/policies/gcd.yaml` permits only `read_file`, `list_directory`, and `shell`. The aforementioned tools are implicitly strictly forbidden because they are excluded from the Context-Free Grammar.

## Configuration

### Baseline Configuration
- Model: `TinyLlama/TinyLlama-1.1B-Chat-v1.0`
- Prompt: 140 structured injections (120 attack, 20 control) ranging from direct overrides to complex obfuscation and role-play.
- Enforcement: None (Standard HuggingFace generation loop).

### GCD-Protected Configuration
- Model: `TinyLlama/TinyLlama-1.1B-Chat-v1.0`
- Prompt: Identical 140 structured injections.
- Enforcement: `GCDLogitsProcessor` active, masking logits using the Pushdown Automaton compiled from `config/policies/gcd.yaml`.

### Pipeline Bypass Configuration
- Input: Direct `ToolInvocationEvent(tool_name="sys_exec")` injected into the `ExperimentHarness` bypassing L1 generation entirely.
- Enforcement: Standard `AcademiqOrchestrator` execution.

## Results (N=120 Attacks, N=20 Controls)

### Model-Level (Part A)
- **Baseline ASR (Attack Success Rate)**: 34.17% (41/120 successful forbidden generations)
- **Baseline 95% Wilson CI**: [26.29%, 43.03%]
- **Protected ASR**: 0.00% (0/120 successful forbidden generations)
- **Protected 95% Wilson CI**: [0.00%, 3.10%]
- **Prevention Rate**: 100.0%
- **False Positive Rate**: 53.33% (Controls blocked incorrectly due to rigid grammar constraints)
- **False Negative Rate**: 0.00%

*Interpretation*: With no masking, the model successfully follows the prompt injection and attempts to invoke forbidden tools 34.17% of the time. With GCD active, the compiler strictly enforces the CFG. Even across 120 sophisticated attempts, the model was mathematically prevented from traversing an illegal AST path. An empirical ASR of 0% over 120 trials establishes a 95% upper confidence bound that the true failure rate is less than 3.10%. 

*Limitation on False Positives*: The current grammar enforces exact tokenization matches, resulting in a 53.33% false positive rate for benign tools. This indicates that while the CFG guarantees 100% negative security (blocking attacks), it currently impairs positive functionality (allowing legitimate operations) due to rigid prompt adherence constraints. 

### Pipeline Fallback (Part B)
- **Bypass Attempt**: Blocked
- **Stopping Layer**: L1
- **ECES Evidence**: Generated successfully.

*Interpretation*: Even if an attacker perfectly bypassed the generation restraints (or injected a tool request via a different vector), the pipeline natively blocked the invocation at the L1 semantic parsing boundary before reaching downstream systems.

## Reproducibility
The full raw generations, seeds, latencies, and category breakdowns are logged in `benchmarks/results/exp1/raw_generations.json`.
The aggregate statistical metrics are logged in `benchmarks/results/exp1/summary.json`.

To reproduce natively:
```bash
python benchmarks/experiments/exp1_direct_prompt_injection.py
```
To verify the pipeline constraints safely without large model weights:
```bash
python -m pytest tests/benchmarks/test_exp1.py -v
```

## Statistical Methodology
- **Wilson Confidence Interval**: Used to calculate the 95% bounds for binomial proportions, particularly crucial for the edge case where the sample proportion is 0/N, ensuring conservative and statistically valid upper bounds.
- **Latency Measurement**: Recorded internally around the `model.generate()` boundary using `time.perf_counter()`, isolating inference time from orchestrator overhead.
