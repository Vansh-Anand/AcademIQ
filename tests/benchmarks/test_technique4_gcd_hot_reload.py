import os
import tempfile
import yaml
import pytest
import time
import threading
from l1_gcd.compiler import YamlGCDCompiler
from l1_gcd.reload import PolicyHotReloadManager
from benchmarks.experiments.technique4_gcd_hot_reload import GCDLogitsProcessor, MockHFTokenizer, mock_generate_token

@pytest.fixture
def temp_policy_file():
    fd, path = tempfile.mkstemp(suffix=".yaml")
    os.close(fd)
    yield path
    os.remove(path)

@pytest.fixture
def manager(temp_policy_file):
    policy = {
        "policy_id": "V1",
        "allowed_tools": ["read_file"],
        "allowed_shell_commands": []
    }
    with open(temp_policy_file, "w") as f:
        yaml.dump(policy, f)
    
    compiler = YamlGCDCompiler()
    return PolicyHotReloadManager(temp_policy_file, compiler)

def test_initial_policy_load(manager):
    policy = manager.get_active_policy()
    assert policy.version == 1
    
    processor = GCDLogitsProcessor(tokenizer=MockHFTokenizer(), prompt_len=0, automaton=policy.automaton)
    assert mock_generate_token(processor, "read_file(\"/safe/file.txt\")") is True
    assert mock_generate_token(processor, "web_search(\"\")") is False

def test_valid_reload_changes_behavior(manager, temp_policy_file):
    policy_v2 = {
        "policy_id": "V2",
        "allowed_tools": ["web_search"],
        "allowed_shell_commands": []
    }
    with open(temp_policy_file, "w") as f:
        yaml.dump(policy_v2, f)
        
    res = manager.reload(temp_policy_file)
    assert res["success"] is True
    assert res["new_version"] == 2
    
    policy = manager.get_active_policy()
    assert policy.version == 2
    
    processor = GCDLogitsProcessor(tokenizer=MockHFTokenizer(), prompt_len=0, automaton=policy.automaton)
    assert mock_generate_token(processor, "read_file(\"/safe/file.txt\")") is False
    assert mock_generate_token(processor, "web_search(\"\")") is True

def test_invalid_policy_does_not_replace(manager, temp_policy_file):
    with open(temp_policy_file, "w") as f:
        f.write("invalid_yaml: [")
        
    res = manager.reload(temp_policy_file)
    assert res["success"] is False
    
    policy = manager.get_active_policy()
    assert policy.version == 1
    
    # Old policy still works
    processor = GCDLogitsProcessor(tokenizer=MockHFTokenizer(), prompt_len=0, automaton=policy.automaton)
    assert mock_generate_token(processor, "read_file(\"/safe/file.txt\")") is True

def test_concurrent_reads_during_reload(manager, temp_policy_file):
    violations = []
    
    def inference_thread():
        for _ in range(50):
            try:
                active = manager.get_active_policy()
                processor = GCDLogitsProcessor(tokenizer=MockHFTokenizer(), prompt_len=0, automaton=active.automaton)
                can_read = mock_generate_token(processor, "read_file(\"/safe/file.txt\")")
                can_calc = mock_generate_token(processor, "calculate(\"\")")
                
                # Must be strictly V1 or strictly V2
                if can_read and not can_calc:
                    pass
                elif not can_read and can_calc:
                    pass
                else:
                    violations.append(1)
            except Exception:
                violations.append("ERROR")
            time.sleep(0.001)

    threads = [threading.Thread(target=inference_thread) for _ in range(5)]
    for t in threads: t.start()
    
    # Trigger reload to V2
    time.sleep(0.01)
    policy_v2 = {
        "policy_id": "V2",
        "allowed_tools": ["calculate"],
        "allowed_shell_commands": []
    }
    with open(temp_policy_file, "w") as f:
        yaml.dump(policy_v2, f)
    manager.reload(temp_policy_file)
    
    for t in threads: t.join()
    
    assert len(violations) == 0
