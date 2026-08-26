# AcademIQ Threat Model

## Assumptions
- The AI Agent executes commands autonomously.
- The AI Agent operates in a possibly untrusted environment.

## L1 Threat Model
- **Threat**: The LLM hallucinates an invalid or malicious tool-call structure.
- **Mitigation**: The GCD guarantees that only syntactically legal tool calls are generated.

## L2 Threat Model
- **Threat (Obfuscation)**: Attackers trick the LLM into generating commands like `$(echo -e '\x72\x6d') /tmp` to bypass static string checks.
- **Mitigation**: The 5-pass normalizer decodes hex/octal/base64, resolves aliases, expands variables, and canonicalizes ASTs securely without evaluating untrusted shell sub-commands.
- **Threat (TOCTOU)**: The LLM/Attacker uses a symlink swap between validation and execution to point a safe path (`/tmp/safe`) to a forbidden path (`/etc/passwd`).
- **Mitigation**: The TOCTOU verifier resolves file identities (inodes) before validation, and verifies the identity right before execution at the execution gate.

## Residual Risks
- Native OS races (e.g. symlink resolution on Windows vs Linux O_PATH) remain platform-specific limitations.
- Highly esoteric, Turing-complete bash subshell evaluations that cannot be statically parsed are forced into an "Unresolved" state, which strictly fails closed.
