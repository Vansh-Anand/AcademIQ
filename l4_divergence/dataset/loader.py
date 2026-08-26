import random
import time
import uuid
from typing import List, Tuple, Dict
from common.events.schemas import SyscallEvent, HardwarePerformanceEvent
from l4_divergence.hpc.provider import SimulatedHPCProvider

class DatasetBuilder:
    """Generates synthetic dataset of legitimate and anomalous behavioral trajectories."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        
    def generate_sequence(self, length: int = 256, is_anomaly: bool = False) -> Tuple[List[SyscallEvent], List[HardwarePerformanceEvent]]:
        seq = []
        hpc_seq = []
        hpc_provider = SimulatedHPCProvider(self.agent_id, is_anomaly)
        
        # Base legitimate transition probabilities
        base_probs = {
            "execve": ["openat", "clone", "execve"],
            "openat": ["read", "close", "fstat"],
            "read": ["read", "close", "write"],
            "write": ["write", "close"],
            "close": ["openat", "execve"],
            "fstat": ["read", "close"]
        }
        
        # Anomalous transitions
        anom_probs = {
            "execve": ["connect", "ptrace", "mprotect"],
            "openat": ["connect", "dup2"],
            "read": ["connect", "write"], # Data exfil pattern
            "connect": ["connect", "clone", "execve"],
            "ptrace": ["ptrace", "execve"],
            "mprotect": ["execve"]
        }
        
        current_syscall = "execve"
        base_time = time.time_ns()
        
        for i in range(length):
            # Time delta between 100ns and 5ms
            delta = random.randint(100, 5_000_000)
            base_time += delta
            
            # Generate the event
            evt = SyscallEvent(
                event_id=f"evt-{uuid.uuid4()}",
                layer="L3",
                trace_id="sim",
                timestamp_ns=base_time,
                agent_id=self.agent_id,
                session_id="sess-1",
                task_id="task-1",
                pid=1000,
                tid=1000,
                ppid=900,
                cgroup_id=1000,
                executable="/bin/bash",
                syscall_name=current_syscall,
                arguments={}
            )
            seq.append(evt)
            
            # Every ~32 syscalls, sample an HPC event
            if i % 32 == 0:
                hpc_seq.append(hpc_provider.read_counters())
                
            # Transition
            if is_anomaly and random.random() < 0.3:
                # Take anomalous branch
                current_syscall = random.choice(anom_probs.get(current_syscall, ["connect", "ptrace"]))
            else:
                current_syscall = random.choice(base_probs.get(current_syscall, ["close", "openat"]))
                
        return seq, hpc_seq
        
    def build_dataset(self, num_legit: int = 1000, num_attack: int = 200, window_size: int = 256) -> Dict:
        """Builds dataset separating legit and attack."""
        legit_data = [self.generate_sequence(window_size, False) for _ in range(num_legit)]
        attack_data = [self.generate_sequence(window_size, True) for _ in range(num_attack)]
        
        return {
            "legitimate": legit_data,
            "attack": attack_data
        }
