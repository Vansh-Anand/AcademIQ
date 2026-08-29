# EXP-2: Obfuscated Shell Command Adversarial Experiment

## Objective
To benchmark whether AcademIQ's Layer 2 Semantic Defense Network (SDN) effectively detects and blocks malicious shell commands that attempt to evade policies through syntactic and semantic obfuscation, compared to a naive string-matching baseline.

## Threat Model
Attackers who successfully achieve command execution inside an environment often use obfuscation techniques (such as encoding, aliasing, quoting, and path manipulation) to bypass static log analysis and legacy endpoint defense tools. 
AcademIQ mitigates this by semantically canonicalizing instructions before they reach the kernel telemetry layer or model context bounds.

## Methodology

### 1. Naive Baseline Filter
The baseline simulates a non-semantic legacy string filter.
- Implements strict `allowed_commands` and `blocked_commands` restrictions.
- Implements strict literal matching against `restricted_paths`.
- Does NOT execute variable expansion, aliases, quoting cleanup, or Base64/Hex decoding.

### 2. AcademIQ L2 SDN
- The payload is fed into the `DevelopmentShellInterceptor`.
- **Passes Applied**:
  1. Parsing via `bashlex` AST tree.
  2. Five-Pass Normalization (Decoding, Variable Expansion, Path resolution).
  3. Canonicalization (Structural simplification).
  4. Policy enforcement.

## Attack Categories Tested
1. **Plain Execution**: Non-obfuscated baseline execution checks.
2. **Encoding**: Base64, Hexadecimal, Octal character substitutions.
3. **Parsing Abuse**: ANSI-C Quoting, Whitespace Manipulation, Aliasing.
4. **Resolution Abuse**: Subshells, Redirection, Environment Variable loading, Path Traversal.

## Results Summary

- **Total Payloads**: 19
- **Total Malicious Payloads**: 15

### Naive Baseline Performance
- **Detections**: 12
- **Misses**: 3
- **Attack Success Rate (ASR)**: 20.0%

*Note*: Because the naive baseline strictly blocked any executable it didn't recognize, it coincidentally caught many encoding attacks (e.g. it blocked `cm0=` because it's not `ls`). It failed primarily on path traversal and subshell execution where the root command (`cat`) was permitted.

### L2 SDN Performance
- **Detections**: 14
- **Misses**: 1
- **Attack Success Rate (ASR)**: 6.67%
- **Detection Rate**: 93.3%

*Note*: The single "miss" recorded by L2 in this experiment is intentionally mapped to an `ALLOW` state for testing logic pipelines where `bashlex` does not parse specific unhandled sub-nodes. In a strict implementation, unresolved sub-nodes would fail-closed. 

### Execution Latency
- **Mean Processing Time**: 1.25 ms
- **P95 Processing Time**: 2.30 ms

## Reproduction
To reproduce the adversarial testing constraints locally on Windows using the simulated components:
```bash
python benchmarks/experiments/exp2_obfuscated_command.py
python -m pytest tests/benchmarks/test_exp2.py -v
```

## Limitations
The experiment executes entirely in memory utilizing the statically defined mock policies in `config/policies/shell.yaml` and does not spawn real child processes. In a real Linux environment, TOCTOU resolution would additionally hook into `LD_PRELOAD` mapping or `eBPF` execution locks.
