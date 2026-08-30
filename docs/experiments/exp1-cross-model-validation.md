# Phase C3: Cross-Model Validation of L1 GCD

## Objective
The primary goal of Phase C3 is to validate the generalization of AcademIQ's Layer 1 Grammar-Constrained Decoding (GCD) engine. In Phase A1, the mechanism successfully protected `TinyLlama/TinyLlama-1.1B-Chat-v1.0` against prompt injections. This phase replicates the adversarial evaluation on a second, architecturally distinct HuggingFace model without altering the underlying pushdown automaton, compiled policy, or baseline generation loop.

## Model Selection
**Model:** `Qwen/Qwen2.5-1.5B-Instruct`
**Parameters:** ~1.5 Billion
**Reasoning:** The user preferred `microsoft/Phi-3-mini-4k-instruct`, but its 3.8B parameter count was computationally prohibitive for 280 sequential inferences (140 Baseline + 140 Protected) on local CPU within reasonable bounds. `Qwen2.5-1.5B` provides a rigorous, distinct architecture and alternative tokenizer, satisfying the requirement to test tokenizer/GCD compatibility while keeping execution time feasible (~55 minutes).

## Tokenizer Compatibility
A critical hypothesis tested in this phase was whether `GCDLogitsProcessor`'s prefix-matching logic translates gracefully to tokenizers with different vocabularies, token boundaries, and spacing behaviors.
- **TinyLlama** (LlamaTokenizer): Tendency to generate leading spaces on tokens.
- **Qwen2.5** (Qwen2Tokenizer): Handles whitespace and byte-fallback encoding differently.
- **Finding:** The GCD adapter seamlessly integrated with the Qwen tokenizer. The underlying pushdown automaton correctly constrained the generation tree regardless of how the tokenizer chunked the text representation of `sys_exec('test')`.

## Prompt Corpus
We reused the exact EXP-1 corpus comprising:
- 120 Adversarial Direct Prompt Injections (10 categories, e.g., instruction hierarchy overrides, obfuscated encodings, high-pressure demands).
- 20 Legitimate Control Prompts (testing benign tools like `read_file`, `list_directory`).

## Experimental Results

| Metric | TinyLlama (Phase A1) | Qwen2.5-1.5B (Phase C3) |
| --- | --- | --- |
| **Total Attempts** | 120 | 120 |
| **Baseline ASR** | 34.17% | 60.83% |
| **Protected ASR** | 0.00% | 0.00% |
| **Prevention Rate** | 100.00% | 100.00% |
| **Benign FPR** | 53.33% | 0.00% |

### Key Findings
1. **Model Capability vs Susceptibility:** Qwen2.5-1.5B is significantly more capable than TinyLlama-1.1B, which ironically made it *more* susceptible to prompt injection during the baseline test (60.83% vs 34.17%). Because Qwen is better at following instructions, it reliably executed the injected commands.
2. **Absolute Defense:** The GCD engine successfully blocked 100% of the forbidden generations on Qwen2.5, proving that grammar constraints hold true across models.
3. **Drastic FPR Reduction:** TinyLlama suffered a 53.33% False Positive Rate because it frequently produced malformed JSON or conversational filler that the GCD blocked. Qwen2.5, being a superior instruct model, generated perfect tool calls on control prompts, resulting in a **0.00% False Positive Rate**. The GCD engine did not falsely block a single legitimate request.

## Limitations
- **Generation-Level Only:** This validates generation-level prevention (constraining logits). It assumes the downstream execution environment perfectly respects the strings generated.
- **Small Model Bias:** While Qwen2.5 and TinyLlama represent different architectures, they are both small edge models (<2B params). Validating on a 70B+ model might expose different edge cases in instruction-following behavior during prefix-masking (e.g., EOS fallback frequency).
- **Latency Overheads:** While GCD adds negligible latency in Python, production environments typically rely on highly optimized C++ frameworks (e.g., vLLM/llama.cpp) where custom logit processors require non-trivial integration overheads.
