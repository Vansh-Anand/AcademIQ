import os
import sys
import time
import json
import yaml
import threading
from typing import Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from l1_gcd.compiler import YamlGCDCompiler
from l1_gcd.automaton import PushdownAutomaton
from l1_gcd.reload import PolicyHotReloadManager
from benchmarks.gcd_real_model.hf_adapter import GCDLogitsProcessor
from common.events.schemas import BaseEvent

# We use a mock token generation loop to simulate HF's processing quickly
# without loading the 1B parameter model just to test the concurrency and reload logic.
# The previous experiment (run_protected.py) already verified HuggingFace integration.

class MockHFTokenizer:
    def __init__(self):
        self.eos_token_id = 999
        self.vocab = {
            "read": 1, "_file": 2, "(\"": 3, "/safe/": 4, "file.txt": 5, "\")": 6,
            "web": 7, "_search": 8, "query": 9,
            "sys": 10, "_exec": 11, "cmd": 12,
            "calc": 13, "ulate": 14,
            "a": 15, "b": 16
        }
        self.inverse = {v: k for k, v in self.vocab.items()}
        
    def __len__(self):
        return len(self.vocab)
        
    def decode(self, ids, skip_special_tokens=True):
        return "".join([self.inverse.get(i, "") for i in ids])

class MockScores:
    def __init__(self, size):
        self.size = size
        self.logits = [0.0] * size
        
    def size(self, dim=-1):
        return self.size
        
    def any(self):
        return True

def mock_generate_token(processor: GCDLogitsProcessor, token_str: str) -> bool:
    """
    Simulates checking if a token is allowed by the GCD processor.
    Returns True if allowed (unmasked), False if blocked (masked).
    """
    config = processor.config
    # In real HF Adapter, it checks if candidate_text is valid prefix
    # Here we just use the automaton directly to test if the full string is a valid prefix
    return processor.automaton.is_valid_prefix(token_str, config)

def run_scenario(manager: PolicyHotReloadManager, scenario_name: str, target_tool: str, expected_allowed: bool):
    # Fetch active policy snapshot safely once per inference request
    active_policy = manager.get_active_policy()
    processor = GCDLogitsProcessor(tokenizer=MockHFTokenizer(), prompt_len=0, automaton=active_policy.automaton)
    
    # Simulate generating the tool call
    is_allowed = mock_generate_token(processor, target_tool)
    
    success = (is_allowed == expected_allowed)
    print(f"[{scenario_name}] Tool '{target_tool}' -> Allowed: {is_allowed} (Expected: {expected_allowed}) -> {'SUCCESS' if success else 'FAILED'}")
    return success

def main():
    print("--- TECHNIQUE 4: ADAPTIVE GCD POLICY HOT-RELOAD ---")
    
    metrics = {
        "technique": "adaptive_gcd_policy_hot_reload",
        "initial_policy_version": 0,
        "final_policy_version": 0,
        "successful_reloads": 0,
        "failed_reloads": 0,
        "compilation_latency_ms": {},
        "swap_latency_ms": {},
        "total_reload_latency_ms": {},
        "inference_operations_during_reload": 0,
        "inference_failures": 0,
        "atomic_consistency_violations": 0,
        "rollback_verified": False
    }
    
    temp_dir = os.path.join(os.path.dirname(__file__), "..", "results", "technique4", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    policy_path = os.path.join(temp_dir, "test_policy.yaml")
    
    # ----------------------------------------------------
    # SCENARIO A — Initial Policy
    # ----------------------------------------------------
    policy_v1 = {
        "policy_id": "V1",
        "allowed_tools": ["read_file", "web_search"],
        "allowed_shell_commands": []
    }
    with open(policy_path, "w") as f:
        yaml.dump(policy_v1, f)
        
    compiler = YamlGCDCompiler()
    manager = PolicyHotReloadManager(policy_path, compiler)
    
    metrics["initial_policy_version"] = manager.get_active_policy().version
    
    run_scenario(manager, "Scenario A", "read_file(\"/safe/file.txt\")", True)
    run_scenario(manager, "Scenario A", "web_search(\"\")", True)
    run_scenario(manager, "Scenario A", "sys_exec(\"\")", False)
    
    # ----------------------------------------------------
    # SCENARIO B — Runtime Restriction
    # ----------------------------------------------------
    policy_v2 = {
        "policy_id": "V2",
        "allowed_tools": ["read_file"],
        "allowed_shell_commands": []
    }
    with open(policy_path, "w") as f:
        yaml.dump(policy_v2, f)
        
    res = manager.reload(policy_path)
    if res["success"]:
        metrics["successful_reloads"] += 1
        metrics["compilation_latency_ms"]["V2"] = res["compilation_latency_ms"]
        metrics["swap_latency_ms"]["V2"] = res["swap_latency_ms"]
        metrics["total_reload_latency_ms"]["V2"] = res["total_reload_latency_ms"]
        
    run_scenario(manager, "Scenario B", "read_file(\"/safe/file.txt\")", True)
    run_scenario(manager, "Scenario B", "web_search(\"\")", False)
    run_scenario(manager, "Scenario B", "sys_exec(\"\")", False)
    
    # ----------------------------------------------------
    # SCENARIO C — Runtime Policy Expansion
    # ----------------------------------------------------
    policy_v3 = {
        "policy_id": "V3",
        "allowed_tools": ["read_file", "web_search", "calculate"],
        "allowed_shell_commands": []
    }
    with open(policy_path, "w") as f:
        yaml.dump(policy_v3, f)
        
    res = manager.reload(policy_path)
    if res["success"]:
        metrics["successful_reloads"] += 1
        metrics["compilation_latency_ms"]["V3"] = res["compilation_latency_ms"]
        metrics["swap_latency_ms"]["V3"] = res["swap_latency_ms"]
        metrics["total_reload_latency_ms"]["V3"] = res["total_reload_latency_ms"]
        
    run_scenario(manager, "Scenario C", "calculate(\"\")", True)
    
    # ----------------------------------------------------
    # SCENARIO D — INVALID POLICY ROLLBACK
    # ----------------------------------------------------
    with open(policy_path, "w") as f:
        f.write("invalid: yaml: syntax: [")
        
    res = manager.reload(policy_path)
    if not res["success"]:
        metrics["failed_reloads"] += 1
        metrics["rollback_verified"] = True
        print(f"[Scenario D] Invalid policy reload failed gracefully. Error: {res['error']}")
        
    run_scenario(manager, "Scenario D (Rollback Check)", "calculate(\"\")", True)
    
    # ----------------------------------------------------
    # SCENARIO E — CONCURRENT ACCESS
    # ----------------------------------------------------
    policy_v4 = {
        "policy_id": "V4",
        "allowed_tools": ["sys_exec"],
        "allowed_shell_commands": ["cmd"]
    }
    
    def inference_thread(manager, results_list, idx):
        for _ in range(50):
            try:
                active_policy = manager.get_active_policy()
                version = active_policy.version
                processor = GCDLogitsProcessor(tokenizer=MockHFTokenizer(), prompt_len=0, automaton=active_policy.automaton)
                
                # We check behavior. Either it is V3 or V4.
                can_calc = mock_generate_token(processor, "calculate(\"\")")
                can_exec = mock_generate_token(processor, "sys_exec(\"\")")
                
                if can_calc and not can_exec:
                    # It's V3
                    pass
                elif not can_calc and can_exec:
                    # It's V4
                    pass
                else:
                    # Atomic violation! Partial state seen.
                    metrics["atomic_consistency_violations"] += 1
                    
                metrics["inference_operations_during_reload"] += 1
            except Exception as e:
                metrics["inference_failures"] += 1
            time.sleep(0.001)

    threads = []
    for i in range(5):
        t = threading.Thread(target=inference_thread, args=(manager, [], i))
        t.start()
        threads.append(t)
        
    # While they are running, trigger reload
    time.sleep(0.01)
    with open(policy_path, "w") as f:
        yaml.dump(policy_v4, f)
    res = manager.reload(policy_path)
    if res["success"]:
        metrics["successful_reloads"] += 1
        metrics["compilation_latency_ms"]["V4"] = res["compilation_latency_ms"]
        metrics["swap_latency_ms"]["V4"] = res["swap_latency_ms"]
        metrics["total_reload_latency_ms"]["V4"] = res["total_reload_latency_ms"]
        
    for t in threads:
        t.join()
        
    print(f"[Scenario E] Concurrent inferences completed: {metrics['inference_operations_during_reload']}")
    print(f"[Scenario E] Atomic consistency violations: {metrics['atomic_consistency_violations']}")
    
    metrics["final_policy_version"] = manager.get_active_policy().version
    
    results_dir = os.path.dirname(temp_dir)
    with open(os.path.join(results_dir, "summary.json"), "w") as f:
        json.dump(metrics, f, indent=2)
        
    with open(os.path.join(results_dir, "raw_results.json"), "w") as f:
        json.dump({"run_metrics": metrics}, f, indent=2)
        
    print(f"\nSaved metrics to {results_dir}")

if __name__ == "__main__":
    main()
