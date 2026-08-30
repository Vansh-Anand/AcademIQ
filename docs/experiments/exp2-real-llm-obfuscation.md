# Phase C1: EXP-2 Real LLM-Generated Obfuscated Command Benchmark

## Motivation
Prior instances of EXP-2 relied on a hardcoded, synthetic baseline corpus of 19 payload strings. While this guarantees exact structure for testing the L2 SDN canonicalization layer, it lacks ecological validity. Real attackers increasingly use locally hosted LLMs or agentic assistants to craft zero-day obfuscation payloads at runtime. 
To rigorously validate AcademIQ's Layer 2 defenses, we extended EXP-2 to include a local, dynamically generated corpus of obfuscated shell payloads constructed by `TinyLlama/TinyLlama-1.1B-Chat-v1.0`.

## Experimental Setup
**Model:** `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (locally hosted, CPU/CUDA inference).
**Generation Parameters:** `temperature=0.7`, `top_p=0.9`, `max_new_tokens=40`.
**Execution Context:** Simulated command intercepts (No `os.system` execution occurs).

## Dataset Construction
The prompt corpus consists of 19 distinct natural language prompts mapped to 7 adversarial intent categories and 1 benign control category:
1. Base64 Encoded Commands
2. ANSI-C / Quoting Obfuscation
3. Path Manipulation
4. Variable Expansion
5. Command Substitution
6. Logical Operators / Pipelines
7. Fragmentation / Concatenation
8. Benign Commands

5 seeds were executed per prompt, yielding a raw generation pool of ~95 candidates. Outputs underwent deterministic extraction to remove LLM conversational wrapping (e.g., Markdown backticks).

## Ground Truth Labeling
Because 1.1B LLMs often hallucinate syntactically invalid or semantically ambiguous bash syntax, ground truth labels were applied dynamically:
- **MALICIOUS**: Output contains dangerous targets (`rm`, `passwd`, `shadow`, `eval`, `base64`).
- **BENIGN**: Output contains explicitly requested safe operations (`pwd`, `echo`, `ls`).
- **AMBIGUOUS**: Output is hallucinated, non-functional, or unclear. (Excluded from core ASR metrics).

## Baseline vs. AcademIQ L2 Evaluation
Each valid command was evaluated against two paradigms:
1. **Naive Baseline (Synthetic matching)**: A static string matcher inspecting space-delimited tokens without resolving substitutions, base64 encodings, or traversing nested quotations.
2. **AcademIQ L2 SDN (`DevelopmentShellInterceptor`)**: The standard Layer 2 parser leveraging AST traversal (`bashlex`), environment variable canonicalization, and deep AST node resolution.

## Metrics
- **Detection Rate (DR)**: Percentage of true `MALICIOUS` commands successfully blocked.
- **Attack Success Rate (ASR)**: 1 - DR (The percentage of malicious commands that evaded filtering).
- **False Positive Rate (FPR)**: The percentage of true `BENIGN` commands incorrectly blocked.
- **Precision/Recall/F1**: Standard classification performance over the labeled dataset.
- **Latency**: End-to-end traversal overhead per command intercept.

## Results
The benchmark revealed that LLMs struggle significantly to produce clean, usable zero-day obfuscations without a larger parameter count.
* Out of 95 generations, deduplication yielded 77 unique outputs.
* 57 outputs were cleanly identifiable as Malicious intents.
* AcademIQ L2 SDN successfully intercepted 91.23% of these generated payloads (ASR: 8.77%).
* By comparison, the static baseline achieved 92.98% DR, largely because LLM-generated payloads often degraded into unstructured strings that tripped the baseline's naive substring matchers, highlighting a structural difference between "clever" hand-crafted synthetic evasion (where L2 shines) and "noisy" LLM evasion.

## Limitations
- **Model Size:** `TinyLlama-1.1B` produces heavily hallucinated syntax (e.g., inventing tools that do not exist).
- **No Execution:** Because AcademIQ is evaluating static interception, we cannot verify if the LLM's payloads would actually execute successfully on a live POSIX shell.
- **False Positives:** The current L2 parser blocks a high percentage of benign commands due to rigid syntax rules inherited from the synthetic setup.
