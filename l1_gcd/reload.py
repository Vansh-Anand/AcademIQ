import time
import hashlib
import yaml
import threading
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .automaton import PushdownAutomaton
from .compiler import YamlGCDCompiler

@dataclass(frozen=True)
class ActivePolicySnapshot:
    version: int
    policy_hash: str
    automaton: PushdownAutomaton
    loaded_timestamp_ns: int
    source_path: str

class PolicyHotReloadManager:
    """
    Manages atomic hot-reloading of GCD PDA policies.
    Guarantees that invalid policies never replace valid ones.
    """
    def __init__(self, initial_policy_path: str, compiler: YamlGCDCompiler):
        self.compiler = compiler
        self.active_policy_snapshot: Optional[ActivePolicySnapshot] = None
        self._reload_lock = threading.Lock()
        
        # Load the initial policy immediately. It must be valid.
        result = self.reload(initial_policy_path)
        if not result["success"]:
            raise ValueError(f"Failed to load initial GCD policy: {result.get('error')}")

    def get_active_policy(self) -> ActivePolicySnapshot:
        """
        Gets the current immutable active policy snapshot.
        This is typically called exactly once per inference request to guarantee consistency.
        """
        return self.active_policy_snapshot

    def _hash_policy(self, policy_content: str) -> str:
        return hashlib.sha256(policy_content.encode("utf-8")).hexdigest()

    def reload(self, policy_path: str) -> Dict[str, Any]:
        """
        Atomically reloads a policy from disk.
        Returns a structured result.
        """
        start_time = time.perf_counter_ns()
        
        # We lock around the reload process to prevent concurrent reloads
        # overriding each other or producing race conditions in version increments.
        with self._reload_lock:
            try:
                # Read candidate policy
                with open(policy_path, "r") as f:
                    policy_content = f.read()
                
                policy_hash = self._hash_policy(policy_content)
                
                # Check if hash is unchanged (optional optimization)
                if self.active_policy_snapshot and self.active_policy_snapshot.policy_hash == policy_hash:
                    latency_ms = (time.perf_counter_ns() - start_time) / 1_000_000
                    return {
                        "success": True,
                        "previous_version": self.active_policy_snapshot.version,
                        "new_version": self.active_policy_snapshot.version,
                        "previous_policy_hash": policy_hash,
                        "new_policy_hash": policy_hash,
                        "compilation_latency_ms": 0,
                        "swap_latency_ms": 0,
                        "total_reload_latency_ms": latency_ms,
                        "message": "Policy hash unchanged. No reload performed."
                    }
                
                policy_config = yaml.safe_load(policy_content)
                
                # Compile new PDA
                compile_start = time.perf_counter_ns()
                grammar = self.compiler.compile_policy(policy_config)
                automaton = PushdownAutomaton(grammar)
                compile_end = time.perf_counter_ns()
                
                # Atomic swap
                swap_start = time.perf_counter_ns()
                
                new_version = 1 if self.active_policy_snapshot is None else self.active_policy_snapshot.version + 1
                prev_version = 0 if self.active_policy_snapshot is None else self.active_policy_snapshot.version
                prev_hash = "" if self.active_policy_snapshot is None else self.active_policy_snapshot.policy_hash
                
                new_snapshot = ActivePolicySnapshot(
                    version=new_version,
                    policy_hash=policy_hash,
                    automaton=automaton,
                    loaded_timestamp_ns=time.time_ns(),
                    source_path=policy_path
                )
                
                # Python object reference assignment is atomic because of the GIL
                self.active_policy_snapshot = new_snapshot
                
                swap_end = time.perf_counter_ns()
                
                return {
                    "success": True,
                    "previous_version": prev_version,
                    "new_version": new_version,
                    "previous_policy_hash": prev_hash,
                    "new_policy_hash": policy_hash,
                    "compilation_latency_ms": (compile_end - compile_start) / 1_000_000,
                    "swap_latency_ms": (swap_end - swap_start) / 1_000_000,
                    "total_reload_latency_ms": (time.perf_counter_ns() - start_time) / 1_000_000
                }
                
            except Exception as e:
                # Rollback behavior: preserve old PDA (by doing nothing)
                prev_version = 0 if self.active_policy_snapshot is None else self.active_policy_snapshot.version
                prev_hash = "" if self.active_policy_snapshot is None else self.active_policy_snapshot.policy_hash
                return {
                    "success": False,
                    "previous_version": prev_version,
                    "new_version": prev_version,
                    "previous_policy_hash": prev_hash,
                    "new_policy_hash": prev_hash,
                    "compilation_latency_ms": 0,
                    "swap_latency_ms": 0,
                    "total_reload_latency_ms": (time.perf_counter_ns() - start_time) / 1_000_000,
                    "error": str(e)
                }
