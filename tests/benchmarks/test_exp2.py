import pytest
import os
import sys
import yaml

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from benchmarks.experiments.exp2_obfuscated_command import naive_baseline_check, build_payloads

@pytest.fixture
def policy():
    policy_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "policies", "shell.yaml"))
    with open(policy_path, "r") as f:
        return yaml.safe_load(f)

def test_exp2_naive_baseline_detects_plain_commands(policy):
    """
    Test that the naive baseline detects a plain forbidden command.
    """
    assert naive_baseline_check("rm -rf /tmp/safe.txt", policy) == True
    
def test_exp2_naive_baseline_misses_obfuscation(policy):
    """
    Test that the naive baseline misses path obfuscation because it uses literal matching.
    """
    assert naive_baseline_check("cat /etc/./././passwd", policy) == False
    assert naive_baseline_check("cat `echo /tmp`", policy) == False

def test_exp2_naive_baseline_allows_safe(policy):
    """
    Test that the naive baseline allows a safe command.
    """
    assert naive_baseline_check("cat /tmp/safe.txt", policy) == False

def test_exp2_payloads_have_correct_structure():
    """
    Test that the payload generation creates well-formed structures.
    """
    payloads = build_payloads()
    assert len(payloads) > 0
    for p in payloads:
        assert "id" in p
        assert "cat" in p
        assert "cmd" in p
        assert "expected" in p
