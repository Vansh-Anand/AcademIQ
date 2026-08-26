# Layer 2: Semantic Defense Network (SDN)

The Semantic Defense Network intercepts commands that have structurally bypassed L1 GCD and evaluates them for semantic safety before passing them to the execution layer. 

## Architecture

1. **Interceptor**: The entry point. Handles `ShellCommandEvent`s.
2. **Parser**: Uses Python's standard `shlex` library to securely tokenize POSIX shell commands, handling quoting and escaping correctly.
3. **Normalizer**: Applies syntactic transformations. E.g., `PathNormalizer` resolves `.` and `..`.
4. **Canonicalizer**: Resolves the exact absolute path and identities of executables and arguments (`os.path.realpath`, `shutil.which`).
5. **TOCTOU Resolver**: Records the `inode` and `device_id` of target paths using `os.stat`. If a path changes identity before execution, the execution layer will abort.
6. **Semantic Policy Matcher**: Evaluates the canonicalized AST against rules defined in `config/policies/sdn.yaml`.

## Platform Limitations (Windows)

The current development environment is Windows 11.
- **TOCTOU**: Linux can use `O_PATH` for robust lockless resolution. On Windows, we rely on checking `st_ino` (FileIndex) and `st_dev` immediately before execution. This is strong but technically not race-free without native handles.
- **Paths**: The canonicalizer ensures cross-platform consistency by mapping `\` to `/` internally after `realpath` resolution. 

## Guarantee

The core guarantee of L2 is `L1 ALLOW + L2 BLOCK = NO EXECUTION`.
A command might successfully pass the Grammar-Constrained Decoding layer, but if it violates semantic policies (e.g. attempting to read a forbidden directory like `/etc`), L2 will issue a `BLOCK` decision and halt the pipeline.
