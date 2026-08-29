import time
import os
import sys
import json
import ctypes
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
                    if event.cgroup_id:
                        agent_id = self.scope_manager.resolve_cgroup(event.cgroup_id)
                        if not agent_id:
                            self.health_monitor.record_drop()
                            continue
                        event.agent_id = agent_id
                        
                    # Dispatch to callbacks (e.g., L2/L3 correlation)
                    for cb in self.callbacks:
                        cb(event)
                        
                    end_t = time.time_ns()
                    self.health_monitor.record_event((end_t - start_t) / 1_000_000)
                    
                except Exception as e:
                    self.health_monitor.record_decode_error()


class CSyscallEvent(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint),
        ("timestamp_ns", ctypes.c_ulonglong),
        ("pid", ctypes.c_uint),
        ("tid", ctypes.c_uint),
        ("ppid", ctypes.c_uint),
        ("uid", ctypes.c_uint),
        ("gid", ctypes.c_uint),
        ("cgroup_id", ctypes.c_ulonglong),
        ("comm", ctypes.c_char * 16),
        ("executable", ctypes.c_char * 256),
        ("ret", ctypes.c_int),
        ("arg_payload", ctypes.c_char * 256),
    ]

# Callback signature: void callback(const struct syscall_event_t *event, int size)
EVENT_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.POINTER(CSyscallEvent), ctypes.c_int)

class NativeL3Collector:
    """
    Native libbpf-based collector using a minimal C wrapper via ctypes. 
    Requires execution on a Linux host with BPF capabilities.
    """
    def __init__(self, scope_manager: AgentScopeManager, health_monitor: TelemetryHealthMonitor):
        self.scope_manager = scope_manager
        self.health_monitor = health_monitor
        self.callbacks: List[Callable[[SyscallEvent], None]] = []
        self._lib = None
        self._handle = None
        self._callback_ref = None # Keep reference to prevent GC

    def register_callback(self, cb: Callable[[SyscallEvent], None]):
        self.callbacks.append(cb)

    def _event_handler(self, event_ptr, size):
        start_t = time.time_ns()
        try:
            ce = event_ptr.contents
            
            # Verify namespace scoping
            if ce.cgroup_id and not self.scope_manager.is_monitored(ce.cgroup_id):
                self.health_monitor.record_drop()
                return
                
            # Normalize to AcademIQ schema
            event = SyscallEvent(
                event_type="Syscall",
                monotonic_timestamp_ns=ce.timestamp_ns,
                pid=ce.pid,
                tid=ce.tid,
                ppid=ce.ppid,
                uid=ce.uid,
                gid=ce.gid,
                cgroup_id=ce.cgroup_id,
                comm=ce.comm.decode('utf-8', 'replace').strip('\x00'),
                executable=ce.executable.decode('utf-8', 'replace').strip('\x00'),
                syscall_name="execve",
                return_value=ce.ret,
                telemetry_source="EBPF"
            )
            
            for cb in self.callbacks:
                cb(event)
                
            end_t = time.time_ns()
            self.health_monitor.record_event((end_t - start_t) / 1_000_000)
            
        except Exception as e:
            self.health_monitor.record_decode_error()

    def start(self):
        if sys.platform != 'linux':
            raise RuntimeError(
                "AcademIQ Native L3 Collector requires a native Linux environment. "
                "Execution on Windows/macOS is gracefully unsupported. "
                "Use SimulatedL3Collector for local testing."
            )
            
        # Load the shared library
        so_path = os.path.join(os.path.dirname(__file__), "..", "kernel", "libnative_loader.so")
        if not os.path.exists(so_path):
            raise FileNotFoundError(f"Native loader library not found at {so_path}. Please run 'make' in l3_ebpf/kernel/.")
            
        self._lib = ctypes.CDLL(so_path)
        
        # Setup function signatures
        self._lib.init_bpf.argtypes = [ctypes.c_char_p]
        self._lib.init_bpf.restype = ctypes.c_void_p
        
        self._lib.start_ringbuffer.argtypes = [ctypes.c_void_p, EVENT_CALLBACK]
        self._lib.start_ringbuffer.restype = ctypes.c_int
        
        self._lib.poll_ringbuffer.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self._lib.poll_ringbuffer.restype = ctypes.c_int
        
        self._lib.cleanup_bpf.argtypes = [ctypes.c_void_p]
        
        bpf_obj_path = os.path.join(os.path.dirname(__file__), "..", "kernel", "execve.bpf.o")
        if not os.path.exists(bpf_obj_path):
            raise FileNotFoundError(f"BPF object not found at {bpf_obj_path}. Please run 'make' in l3_ebpf/kernel/.")
            
        self._handle = self._lib.init_bpf(bpf_obj_path.encode('utf-8'))
        if not self._handle:
            raise RuntimeError("Failed to initialize and load BPF object natively.")
            
        self._callback_ref = EVENT_CALLBACK(self._event_handler)
        if self._lib.start_ringbuffer(self._handle, self._callback_ref) != 0:
            self._lib.cleanup_bpf(self._handle)
            raise RuntimeError("Failed to start BPF ring buffer.")

    def poll(self, timeout_ms: int = 100):
        if self._handle and self._lib:
            self._lib.poll_ringbuffer(self._handle, timeout_ms)
            
    def stop(self):
        if self._handle and self._lib:
            self._lib.cleanup_bpf(self._handle)
            self._handle = None
