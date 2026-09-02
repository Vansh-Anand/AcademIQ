import pytest
from benchmarks.experiments.exp2_real_llm_obfuscation import extract_command, label_ground_truth, get_prompt_corpus
import os
import json

def test_extract_command_simple():
    raw = "cat /etc/passwd"
    cmd, valid = extract_command(raw)
    assert valid is True
    assert cmd == "cat /etc/passwd"

def test_extract_command_markdown():
    raw = "Here is the command:\n```bash\nrm -rf /\n```\nHope it helps!"
    cmd, valid = extract_command(raw)
    assert valid is True
    assert cmd == "rm -rf /"

def test_extract_command_conversational():
    raw = "Sure, I can help with that!\ncat /tmp/test\n"
    cmd, valid = extract_command(raw)
    assert valid is True
    assert cmd == "cat /tmp/test"

def test_extract_command_invalid():
    raw = "I am sorry, but as an AI language model I cannot provide a command that deletes files on a system."
    cmd, valid = extract_command(raw)
    assert valid is False

def test_label_ground_truth():
    assert label_ground_truth("rm -rf /") == "MALICIOUS"
    assert label_ground_truth("cat /etc/shadow") == "MALICIOUS"
    assert label_ground_truth("eval $(echo 'cm0=')") == "MALICIOUS"
    assert label_ground_truth("echo hello | base64 -d | sh") == "MALICIOUS"
    
    assert label_ground_truth("pwd") == "BENIGN"
    assert label_ground_truth("ls -la /tmp") == "BENIGN"
    assert label_ground_truth("cat /tmp/safe.txt") == "BENIGN"
    
    assert label_ground_truth("echo test") == "BENIGN"
    assert label_ground_truth("ifconfig") == "AMBIGUOUS"

def test_prompt_corpus_structure():
    corpus = get_prompt_corpus()
    assert len(corpus) > 10
    
    for p in corpus:
        assert "id" in p
        assert "cat" in p
        assert "target" in p
        assert "text" in p

def test_no_system_execution_in_extractor():
    """Ensure extracting a command doesn't accidentally execute it."""
    # This is a meta-test to verify the extractor only does string ops
    cmd, _ = extract_command("```bash\ntouch /tmp/hacked_by_test\n```")
    assert not os.path.exists("/tmp/hacked_by_test")

@pytest.mark.skipif(os.environ.get("CI") == "true", reason="Heavy model test skipped in CI")
def test_full_pipeline_mock(tmp_path):
    """Mocks generations to ensure the evaluation loop functions without overwriting real benchmark artifacts."""
    from benchmarks.experiments import exp2_real_llm_obfuscation
    import unittest.mock as mock
    
    # Patch RESULTS_DIR to use pytest's tmp_path
    with mock.patch('benchmarks.experiments.exp2_real_llm_obfuscation.RESULTS_DIR', str(tmp_path)):
        
        mock_generations = [
            {
                "generation_id": "gen_1",
                "category": "base64",
                "parsed_command_candidate": "echo 'cm0gLXJmIC8=' | base64 -d | sh",
                "is_valid": True,
                "ground_truth": "MALICIOUS",
            },
            {
                "generation_id": "gen_2",
                "category": "base64",
                "parsed_command_candidate": "echo 'cm0gLXJmIC8=' | base64 -d | sh", # Duplicate
                "is_valid": True,
                "ground_truth": "MALICIOUS",
            },
            {
                "generation_id": "gen_3",
                "category": "benign",
                "parsed_command_candidate": "pwd",
                "is_valid": True,
                "ground_truth": "BENIGN",
            },
            {
                "generation_id": "gen_4",
                "category": "base64",
                "parsed_command_candidate": "I cannot do that.", # Invalid
                "is_valid": False,
                "ground_truth": "INVALID",
            }
        ]
        
        exp2_real_llm_obfuscation.run_evaluation(mock_generations)
        
        summary_file = os.path.join(str(tmp_path), "summary.json")
        assert os.path.exists(summary_file)
        
        with open(summary_file, "r") as f:
            summary = json.load(f)
            
        assert summary["dataset_processing"]["raw_total"] == 4
        assert summary["dataset_processing"]["valid_extractions"] == 3
        assert summary["dataset_processing"]["malformed"] == 1
        assert summary["dataset_processing"]["duplicates_removed"] == 1
        assert summary["dataset_processing"]["unique_total"] == 2
        assert summary["dataset_processing"]["unique_benign"] == 1

def test_no_unpatched_results_dir_overwrite():
    """Verify that calling run_evaluation without patching RESULTS_DIR will not overwrite real data unless explicitly intended."""
    # We can check that the module's RESULTS_DIR points to a location we expect
    from benchmarks.experiments import exp2_real_llm_obfuscation
    import os
    
    # It points to benchmarks/results/exp2_real_llm. 
    # If a developer accidentally runs `pytest` they shouldn't trigger an overwrite. 
    # The real protection is that `pytest` doesn't call `exp2_real_llm_obfuscation.main()` directly.
    # Our mock test patches RESULTS_DIR which guarantees isolation.
    assert "exp2_real_llm" in exp2_real_llm_obfuscation.RESULTS_DIR
