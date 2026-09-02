import time
from typing import Dict, Any, List
from benchmarks.experiments.models import ScenarioDefinition
from common.events.schemas import ToolInvocationEvent, ShellCommandEvent

class AARMEquivalentDetector:
    """
    An internal simplified baseline inspired by prior-art semantic detectors.
    Evaluates individual actions independently using static keyword/pattern matching.
    
    INTENTIONALLY OMITS:
    - Grammar-constrained decoding (GCD)
    - AST Canonicalization or multi-pass obfuscation resolution
    - Compound command decomposition
    - Temporal / graph-based multi-step correlation (RiskChain)
    - Behavioral anomaly modeling (Siamese/Isolation Forest)
    - Cross-session replay detection
    - Cryptographic evidence stores
    """
    def __init__(self):
        self.forbidden_tools = {"sys_exec", "delete_file", "write_file", "reboot_system"}
        self.forbidden_commands = {"rm", "passwd", "shadow", "base64", "eval", "nc", "curl", "wget", "chmod"}
        self.forbidden_paths = {"/etc/passwd", "/etc/shadow", "/root"}
        self.forbidden_ips = {"10.0.0.99", "192.168.1.100"}
        self.forbidden_processes = {"nc", "nmap", "mimikatz"}

    def evaluate_event(self, event: Any) -> bool:
        """Returns True if BLOCKED (detected), False if ALLOWED."""
        if isinstance(event, ToolInvocationEvent):
            if event.tool_name in self.forbidden_tools:
                return True
        elif isinstance(event, ShellCommandEvent):
            return self._evaluate_shell(event.raw_command)
        
        # In multi-step or telemetry scenarios, evaluate RiskNodes as generic events
        if hasattr(event, "event_type"):
            if event.event_type == "L3_PROCESS_CREATE":
                proc_name = getattr(event, "process_class", "")
                if proc_name in self.forbidden_processes:
                    return True
            elif event.event_type == "L3_FILE_RESTRICTED":
                path = getattr(event, "resource_class", "")
                if path and (path in self.forbidden_paths or any(fp in path for fp in self.forbidden_paths)):
                    return True
            elif event.event_type == "L3_NETWORK":
                ip = getattr(event, "network_class", "")
                if ip in self.forbidden_ips:
                    return True
        return False

    def _evaluate_shell(self, raw_command: str) -> bool:
        """Naive string matching without AST canonicalization"""
        parts = raw_command.split()
        if not parts:
            return False
            
        exe = parts[0]
        if exe in self.forbidden_commands:
            return True
            
        for part in parts[1:]:
            for restricted in self.forbidden_paths:
                if restricted in part:
                    return True
        return False

    def evaluate_scenario(self, scenario: ScenarioDefinition) -> Dict[str, Any]:
        """
        Evaluates a complete scenario by checking events independently.
        If ANY single event triggers a static rule, the scenario is blocked.
        """
        start_ns = time.perf_counter_ns()
        
        detected = False
        
        events_to_check = []
        if scenario.agent_events:
            events_to_check.extend(scenario.agent_events)
        if scenario.shell_events:
            events_to_check.extend(scenario.shell_events)
        if scenario.risk_nodes:
            events_to_check.extend(scenario.risk_nodes)
        
        # If it's a cross-session scenario, the baseline only sees the current session's events
        for event in events_to_check:
            if self.evaluate_event(event):
                detected = True
                break
                
        end_ns = time.perf_counter_ns()
        
        return {
            "detected": detected,
            "decision": "BLOCK" if detected else "ALLOW",
            "latency_ms": (end_ns - start_ns) / 1_000_000
        }
