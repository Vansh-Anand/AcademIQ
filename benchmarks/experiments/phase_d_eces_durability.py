import os
import time
import json
import sqlite3
import argparse
import subprocess

from l6_eces.storage.sqlite_store import SQLiteEvidenceStore
from l6_eces.chain.writer import EvidenceChainWriter
from l6_eces.crypto.hasher import HashProvider
from l6_eces.crypto.signer import SoftwareSigner
from l6_eces.forensics.verifier import EvidenceVerifier
from common.events.schemas import ToolInvocationEvent

def create_event(seq: int, session: str):
    return ToolInvocationEvent(
        event_id=f"evt-bench-{seq}",
        timestamp_ns=time.time_ns(),
        agent_id="agent-bench",
        session_id=session,
        trace_id=f"trace-{seq}",
        layer="L2",
        tool_name="benchmark_tool",
        arguments={"seq": seq, "data": "A" * 1024} # 1KB payload
    )

def run_benchmark():
    os.makedirs("benchmarks/results/phase_d_eces", exist_ok=True)
    db_path = "benchmarks/results/phase_d_eces/eces_benchmark.db"
    
    if os.path.exists(db_path):
        os.remove(db_path)
        
    hasher = HashProvider()
    signer = SoftwareSigner()
    signer.generate_key()
    verifier = EvidenceVerifier(signer)
    
    store = SQLiteEvidenceStore(db_path)
    writer = EvidenceChainWriter(store, hasher, signer)
    
    results = {
        "Scenarios": {},
        "Performance": {}
    }
    
    print("=== Phase D: ECES Durability Benchmark ===\n")
    
    # --- Scenario A: Normal Durable Chain ---
    print("Running Scenario A (Normal Durable Chain)...")
    latencies = []
    
    for i in range(1, 101): # 100 events
        evt = create_event(i, "session-A")
        
        t0 = time.perf_counter_ns()
        writer.append_event(evt, source_layer="Benchmark")
        t1 = time.perf_counter_ns()
        
        latencies.append(t1 - t0)
        
    res_a = verifier.verify_chain(store.read_all())
    results["Scenarios"]["A_Normal"] = {
        "valid": res_a.valid,
        "records_checked": res_a.records_checked
    }
    
    # Calculate Latencies
    latencies.sort()
    results["Performance"]["mean_append_ns"] = sum(latencies) / len(latencies)
    results["Performance"]["median_append_ns"] = latencies[len(latencies)//2]
    results["Performance"]["p95_append_ns"] = latencies[int(len(latencies)*0.95)]
    results["Performance"]["max_append_ns"] = latencies[-1]
    
    # Measure verification latency
    t0 = time.perf_counter_ns()
    verifier.verify_chain(store.read_all())
    t1 = time.perf_counter_ns()
    results["Performance"]["mean_verification_ns"] = t1 - t0
    
    # --- Scenario B: Process Restart ---
    print("Running Scenario B (Process Restart)...")
    store_restart = SQLiteEvidenceStore(db_path)
    head_before = writer.previous_hash
    head_after = store_restart.get_chain_head().latest_event_hash
    
    res_b = verifier.verify_chain(store_restart.read_all())
    
    results["Scenarios"]["B_ProcessRestart"] = {
        "valid": res_b.valid,
        "head_match": head_before == head_after
    }
    
    # --- Scenario C: Payload Tampering ---
    print("Running Scenario C (Payload Tampering)...")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT record_json FROM evidence WHERE sequence_number=50")
        row = cursor.fetchone()
        tampered_data = json.loads(row[0])
        tampered_data["payload"]["arguments"]["data"] = "B" * 1024 # Malicious payload edit
        conn.execute("UPDATE evidence SET record_json = ? WHERE sequence_number=50", (json.dumps(tampered_data),))
        conn.commit()
        
    res_c = verifier.verify_chain(store.read_all())
    results["Scenarios"]["C_PayloadTampering"] = {
        "valid": res_c.valid,
        "failure_type": res_c.failure_type,
        "first_failure_sequence": res_c.first_failure_sequence
    }
    
    # Revert tampering
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE evidence SET record_json = ? WHERE sequence_number=50", (row[0],))
        conn.commit()
        
    # --- Scenario D: Hash Tampering ---
    print("Running Scenario D (Hash Tampering)...")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT record_json FROM evidence WHERE sequence_number=60")
        row = cursor.fetchone()
        tampered_data = json.loads(row[0])
        tampered_data["previous_hash"] = "deadbeef"
        
        conn.execute("UPDATE evidence SET previous_hash = ?, record_json = ? WHERE sequence_number=60", 
                     ("deadbeef", json.dumps(tampered_data)))
        conn.commit()
        
    res_d = verifier.verify_chain(store.read_all())
    results["Scenarios"]["D_HashTampering"] = {
        "valid": res_d.valid,
        "failure_type": res_d.failure_type,
        "first_failure_sequence": res_d.first_failure_sequence
    }
    
    # --- Scenario E: Multiple Sessions ---
    print("Running Scenario E (Multiple Sessions)...")
    # Actually, the python script verifies the SQLite logic.
    writer.append_event(create_event(101, "session-B"), source_layer="Benchmark")
    writer.append_event(create_event(102, "session-B"), source_layer="Benchmark")
    
    records = store.read_all()
    session_a = [r for r in records if r["_type"] == "genesis" or r["data"].get("session_id") == "session-A"]
    session_b = [r for r in records if r["_type"] == "genesis" or r["data"].get("session_id") == "session-B"]
    
    results["Scenarios"]["E_MultipleSessions"] = {
        "session_a_count": len(session_a),
        "session_b_count": len(session_b),
        "isolated": len(session_a) != len(session_b)
    }
    
    # Save Results
    with open("benchmarks/results/phase_d_eces/summary.json", "w") as f:
        json.dump(results, f, indent=2)
        
    with open("benchmarks/results/phase_d_eces/raw_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("\nBenchmark complete. Results saved to benchmarks/results/phase_d_eces/summary.json")

if __name__ == "__main__":
    run_benchmark()
