# Layer 2: Semantic Defense Network (SDN)

The Semantic Defense Network intercepts commands that have structurally bypassed L1 GCD and evaluates them for semantic safety before passing them to the execution layer. It relies on a rigorous 5-pass normalization algorithm to resolve obfuscation statically.

## Architecture

1. **Interceptor**: The entry point (`ShellInterceptor`). Uses `LinuxLDPreloadInterceptor` or `LinuxEBPFUprobeInterceptor` structurally in production, simulated in development.
2. **Parser**: Uses Python's `bashlex` library to tokenize POSIX shell commands safely into an AST.
3. **Five-Pass Normalizer**:
    - **Pass 1 - Variable Expansion**: Safe, static resolution of environment variables against a predefined `SafeEnvironmentSnapshot`.
    - **Pass 2 - Encoding Decode**: Detects and decodes HEX, OCTAL, BASE64, and URL encoding safely without executing anything.
    - **Pass 3 - ANSI-C Quoting**: Normalizes strings like `$'r\x6d'` into `rm`.
    - **Pass 4 - Alias/Function Resolution**: Applies known aliases from a safe shell metadata snapshot.
    - **Pass 5 - Canonicalization**: Implements strict path and argument canonicalization.
4. **Policy Matcher**: Evaluates the `CanonicalCommand` against rules defined in `config/policies/shell.yaml` using a fast evaluator.
5. **TOCTOU Resolver**: Records the `inode` and `device_id` of target paths using `os.stat`. 
6. **Execution Gate**: Strictly enforces `L1 ALLOW + L2 BLOCK = NO EXECUTION`.

## Static Validation Model

Crucially, **no command execution occurs during normalization**. Command substitutions like `$(rm -rf /)` are marked as unresolved. In strict mode, unresolved substitutions trigger a hard `BLOCK` to fail closed.

## Platform Limitations (Windows)

- **TOCTOU**: Linux can use `O_PATH` for robust lockless resolution. On Windows, we rely on checking `st_ino` (FileIndex) and `st_dev` immediately before execution.
- **Paths**: The canonicalizer ensures cross-platform consistency by mapping `\` to `/` internally after `realpath` resolution. Native LD_PRELOAD interceptors are merely structurally mocked on Windows.

## Event Schema

L2 emits `NormalizedCommandEvent` containing the original hash, the canonical hash, the trace of all normalization transformations applied, TOCTOU resolution locks, and the ultimate `SecurityDecision`.
