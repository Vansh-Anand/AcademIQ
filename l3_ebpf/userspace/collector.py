import time
import os
import json
from typing import List, Callable
from common.events.schemas import SyscallEvent
from l3_ebpf.namespace.scope import AgentScopeManager
from l3_ebpf.userspace.health import TelemetryHealthMonitor

class SimulatedL3Collector:
    """
    Simulates eBPF ring buffer telemetry on a Windows host or non-root Linux environment.
    Reads from a predefined trace file and feeds SyscallEvents into the pipeline.
    """
    def __init__(self, scope_manager: AgentScopeManager, health_monitor: TelemetryHealthMonitor, trace_file: str):
        self.scope_manager = scope_manager
        self.health_monitor = health_monitor
        self.trace_file = trace_file
        self.callbacks: List[Callable[[SyscallEvent], None]] = []
        
    def register_callback(self, cb: Callable[[SyscallEvent], None]):
        self.callbacks.append(cb)
        
    def run_replay(self):
        """Simulates polling the eBPF ringbuffer"""
        if not os.path.exists(self.trace_file):
            raise FileNotFoundError(f"Simulation trace file not found: {self.trace_file}")
            
        with open(self.trace_file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                start_t = time.time_ns()
                
                try:
                    data = json.loads(line)
                    event = SyscallEvent(**data)
                    
                    # Verify namespace scoping
                    if event.cgroup_id and not self.scope_manager.is_monitored(event.cgroup_id):
                        self.health_monitor.record_drop()
                        continue
                        
                    # Dispatch to callbacks (e.g., L2/L3 correlation)
                    for cb in self.callbacks:
                        cb(event)
                        
                    end_t = time.time_ns()
                    self.health_monitor.record_event((end_t - start_t) / 1_000_000)
                    
                except Exception as e:
                    self.health_monitor.record_decode_error()


class NativeL3Collector:
    """
    Stub for the native libbpf-based collector. 
    On Windows, this immediately fails.
    """
    def __init__(self, scope_manager: AgentScopeManager, health_monitor: TelemetryHealthMonitor):
        self.scope_manager = scope_manager
        self.health_monitor = health_monitor
        
    def start(self):
        if os.name == 'nt':
            raise RuntimeError(
                "AcademIQ Native L3 Collector cannot run on Windows. "
                "Use the SimulatedL3Collector for local testing, or deploy to a Native Linux environment. "
                "See docs/l3-ebpf.md for details."
            )
        else:
            raise NotImplementedError("Native libbpf python bindings require ctypes/cffi setup out of scope for Phase 4 prototype.")
