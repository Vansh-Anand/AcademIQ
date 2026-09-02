import json
import os
import sys

def validate_registry():
    registry_path = os.path.join(os.path.dirname(__file__), "..", "..", "benchmarks", "results", "experiment_registry.json")
    
    if not os.path.exists(registry_path):
        print(f"Registry not found at {registry_path}")
        sys.exit(1)
        
    with open(registry_path, "r") as f:
        data = json.load(f)
        
    assert "schema_version" in data
    assert "generated_at" in data
    assert "experiments" in data
    assert "historical_discrepancies" in data
    
    seen_ids = set()
    
    for exp in data["experiments"]:
        exp_id = exp["experiment_id"]
        print(f"Validating {exp_id}...")
        
        # Check no duplicate canonical experiment IDs
        assert exp_id not in seen_ids, f"Duplicate experiment ID: {exp_id}"
        seen_ids.add(exp_id)
        
        # Check valid execution_mode
        assert exp["execution_mode"] in ["REAL_RUNTIME", "SIMULATED", "SYNTHETIC", "BENCHMARK", "UNAVAILABLE"], f"Invalid execution_mode in {exp_id}"
        
        # Check numeric metrics
        dr = exp["detection_rate"]
        asr = exp["attack_success_rate"]
        fpr = exp["false_positive_rate"]
        
        if dr is not None:
            assert 0 <= dr <= 100, f"DR out of bounds in {exp_id}"
        if asr is not None:
            assert 0 <= asr <= 100, f"ASR out of bounds in {exp_id}"
        if fpr is not None:
            assert 0 <= fpr <= 100, f"FPR out of bounds in {exp_id}"
            
        # Check counts
        samples = exp["sample_count"]
        malicious = exp["malicious_count"]
        benign = exp["benign_count"]
        
        if samples is not None:
            assert samples >= 0, f"Negative samples in {exp_id}"
        if malicious is not None:
            assert malicious >= 0, f"Negative malicious in {exp_id}"
        if benign is not None:
            assert benign >= 0, f"Negative benign in {exp_id}"
            
        if samples is not None and malicious is not None and benign is not None:
            # We don't assert samples == malicious + benign strictly, 
            # as there might be ambiguous/invalid/partial. But it shouldn't exceed.
            assert malicious + benign <= samples, f"Counts exceed samples in {exp_id}"
            
        # Check references
        source_artifact = exp.get("source_artifact")
        if source_artifact:
            assert os.path.exists(os.path.join(os.path.dirname(__file__), "..", "..", source_artifact)), f"Source artifact not found for {exp_id}"
            
        script = exp.get("experiment_script")
        if script:
            assert os.path.exists(os.path.join(os.path.dirname(__file__), "..", "..", script)), f"Script not found for {exp_id}"

    # Required experiment IDs
    required_ids = ["EXP-1", "EXP-2A", "EXP-2B", "EXP-3", "EXP-4", "EXP-5", "EXP-6"]
    for req_id in required_ids:
        assert req_id in seen_ids, f"Missing required experiment {req_id}"

    print("Experiment registry is valid.")

if __name__ == "__main__":
    validate_registry()
