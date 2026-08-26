# AcademIQ Phase 4: L3 eBPF Kernel Probe & Telemetry

## Overview
Phase 4 implements the host-only telemetry and monitoring layer of the AcademIQ interceptor using Linux eBPF.
This ensures that AcademIQ accurately observes and correlates agent actions directly at the kernel boundary, immune to userspace evasion.

## Components
- **Kernel eBPF Probes** (`l3_ebpf/kernel/`): C programs compiled to eBPF bytecode that hook into `sys_enter_execve`, `sys_enter_openat`, etc., using a ring buffer map.
- **Scope Manager** (`l3_ebpf/namespace/scope.py`): Enforces cgroup boundaries to restrict telemetry to the specific container running the AI agent, protecting host privacy.
- **Correlation Manager** (`l3_ebpf/userspace/correlation.py`): Fuses `NormalizedCommandEvent` (L2) with `SyscallEvent` (L3) to detect unapproved execution or shell breakouts.
- **Enforcement Manager** (`l3_ebpf/enforcement/kernel.py`): Exerts host-level control (SIGSTOP/SIGKILL) over the offending cgroup when anomalies occur, supporting signed-resume cryptography.

## Simulation Mode
Since this prototype is developed on Windows, native eBPF execution is disabled. A rigorous `SimulatedL3Collector` parses pre-recorded `SyscallEvent` streams (JSONL traces) to test the correlation pipeline natively on Windows.

To run tests:
```bash
python -m pytest tests/integration/test_l3_ebpf.py -v
```
