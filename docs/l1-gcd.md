# Layer 1: Grammar-Constrained Decoding (GCD)

GCD is the first and most robust line of defense in AcademIQ.

## Why it exists
LLMs can generate arbitrary tokens, and post-generation filters are subject to prompt injection evasions, TOCTOU races, and parsing discrepancies. GCD enforces syntax strictly at generation time.

## Mechanism
1. **Security Policy**: Admins define allowed/forbidden tools and arguments.
2. **CFG**: The compiler generates a Context-Free Grammar.
3. **PDA**: A Pushdown Automaton simulates the grammar state.
4. **Logit Masking**: At inference, the vocabulary is scanned. Tokens representing illegal grammatical continuations receive a probability penalty of `-∞` before the Softmax function.
5. **Softmax**: Mathematically guarantees $P(forbidden) = 0$.

## Ollama Limitation
Ollama's current API does not expose a hook for manipulating raw logits before the softmax sampling occurs. Therefore, the Ollama adapter in AcademIQ is marked with `supports_pre_softmax_masking = False`. To use the true hard-GCD constraint, a HuggingFace pipeline (or similar framework exposing logits) is required.

## Fail-Safe
If the GCD engine fails to find any legal tokens (`GCD_NO_LEGAL_TOKEN`), the pipeline blocks the generation rather than reverting to unconstrained output.
