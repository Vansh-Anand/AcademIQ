# L3 Native Linux Gap Analysis

## 1. Current Implementation
The current implementation of Layer 3 (eBPF Telemetry) is fundamentally a **Windows-compatible simulation stub**. While there is a single native `.bpf.c` program written in C, it is not actually wired into the Python pipeline for live tracing. The python collector reads static JSON trace files instead.

## 2. Actual Tracepoints Implemented
- **Implemented in C**: `tracepoint/syscalls/sys_enter_execve`

## 3. Event Schema
- **Missing Tracepoints Mentioned in Target Architecture**: `sys_enter_openat`, `sys_enter_socket`, `sys_enter_connect`, `sys_enter_clone`, `sys_enter_ptrace`. (Note: `events.h` has enums for `OPENAT` and `CONNECT`, but no BPF logic).
- **Structure**: `type`, `timestamp_ns`, `pid`, `tid`, `ppid`, `uid`, `gid`, `cgroup_id`, `comm`, `executable`, `ret`, `arg_payload`.
- **Return Codes**: Not captured. Tracepoint is `sys_enter` where return codes don't exist yet, and `ret` is ignored.
- **Arguments**: Only `executable` (arg 0) is captured. The rest of the payload array is stubbed out (hardcoded to `\0`).
- **Argument Hashing**: Not implemented.

## 4. BPF Maps
- **Ring Buffer**: `BPF_MAP_TYPE_RINGBUF` (Implemented, size: 256 KB)
- **Cgroup Filter**: `BPF_MAP_TYPE_HASH` (Used to filter events by `cgroup_id`)

## 5. Userspace Collector
- **NativeL3Collector**: Raises `NotImplementedError` regarding ctypes/cffi bindings for libbpf.
- **SimulatedL3Collector**: Functional, but strictly reads from `.jsonl` trace files. The Python pipeline has zero capability to interact with live eBPF maps or ring buffers.

## 6. Build System
- **Makefile**: Simply runs `clang -target bpf` and `llvm-strip`. It does not handle BPF skeleton generation (like `bpftool gen skeleton`) which would be necessary for standard libbpf deployments without BCC.
- **vmlinux.h**: Expected by the C code, but missing from the repository (assumed to be dumped locally on a target Linux machine).

## 7. Namespace/Cgroup Isolation
- BPF filtering logic exists in C (drops events not matching the `cgroup_filter` map), but **Python never populates this map**. `AgentScopeManager` manages scopes locally in Python space but lacks the bridge to update the eBPF kernel maps.

## 8. Enforcement
- `KernelEnforcementManager` relies on Python's `os.kill()` to send `SIGSTOP` and `SIGKILL`. It is not utilizing eBPF helpers (like `bpf_send_signal()`) for synchronous kernel-level enforcement.

## 9. Testing
- `test_l3_ebpf.py` exclusively tests `SimulatedL3Collector` using a mocked telemetry trace (`execve_trace.jsonl`). Native attachment is completely untested.

## 10. Gaps Against Target Architecture
1. Five out of six required probes are missing.
2. No live python-to-libbpf communication (Ringbuffer reads, Map updates).
3. Syscall arguments are partially ignored.
4. No exit hooks (`sys_exit`) to capture return codes.
5. Enforcement is userspace-dependent rather than synchronous in-kernel.

## 11. Minimal Required Changes
To move toward real Linux validation, the Python pipeline must be able to load and attach the compiled BPF object and continuously poll the ring buffer. Given the missing bindings for `libbpf`, switching the script to use `bcc` (BPF Compiler Collection) might be the fastest bridge for prototyping natively in Python, or a C-extension must be written.

## 12. Linux Dependencies
- `clang`, `llvm`, `bpftool` (for vmlinux.h)
- `python3-bpfcc` / `bcc-tools` (if using BCC)
- Linux Kernel 5.8+ (for Ring Buffer support)

## 13. Risks/Limitations
- Relying on `sys_enter` means the system blocks or correlates actions *before* the kernel verifies permissions, which is good for TOCTOU but means `ret` codes cannot be logged accurately unless paired with `sys_exit` tracepoints.
