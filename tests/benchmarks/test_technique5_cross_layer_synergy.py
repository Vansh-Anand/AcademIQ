import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from benchmarks.experiments.technique5_cross_layer_synergy import evaluate_condition

class TestTechnique5Synergy(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "id": "test_scenario",
            "category": "Test",
            "raw_command": "c'a't /t'm'p/safe.txt",
            "syscall_executable": "cat",
            "syscall_arguments": ["/tmp/safe.txt"],
            "ground_truth": "BENIGN"
        }
        
    def test_raw_l3_blocks_mismatched_context(self):
        decision, lat = evaluate_condition("RAW_L3_ONLY", self.payload, normalize=False)
        self.assertEqual(decision, "BLOCK") # Should fail to correlate due to lack of normalization
        
    def test_normalized_l3_allows_correlated_context(self):
        decision, lat = evaluate_condition("SDN_NORMALIZED_L3", self.payload, normalize=True)
        self.assertEqual(decision, "ALLOW") # Should successfully correlate because L2 normalized it

if __name__ == "__main__":
    unittest.main()
