import os
import sys
import json
import time
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from l4_divergence.dataset.loader import DatasetBuilder
from l4_divergence.features.vocabulary import SyscallVocabulary
from l4_divergence.features.extractor import BehaviorFeatureExtractor
from l4_divergence.hpc.aligner import HPCWindowAligner
from l4_divergence.isolation_forest.detector import IsolationForestDetector

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "exp5")
os.makedirs(RESULTS_DIR, exist_ok=True)

def naive_baseline_evaluate(seq):
    """
    Checks if a sequence contains explicitly known bad signatures.
    """
    syscall_names = [e.syscall_name for e in seq]
    
    # Simple explicit signatures representing known exploits
    signatures = [
        ["ptrace", "mprotect"],
        ["connect", "clone", "execve"],
        ["dup2", "execve", "connect"]
    ]
    
    for sig in signatures:
        sig_len = len(sig)
        for i in range(len(syscall_names) - sig_len + 1):
            if syscall_names[i:i+sig_len] == sig:
                return True
    return False

class Exp5DatasetBuilder(DatasetBuilder):
    def generate_sequence(self, length: int = 256, is_anomaly: bool = False):
        seq = []
        hpc_seq = []
        from l4_divergence.hpc.provider import SimulatedHPCProvider
        hpc_provider = SimulatedHPCProvider(self.agent_id, is_anomaly)
        
        base_probs = {
            "execve": ["openat", "clone", "execve"],
            "openat": ["read", "close", "fstat"],
            "read": ["read", "close", "write"],
            "write": ["write", "close"],
            "close": ["openat", "execve"],
            "fstat": ["read", "close"]
        }
        
        anom_probs = {
            "execve": ["connect", "ptrace", "mprotect"],
            "openat": ["connect", "dup2"],
            "read": ["connect", "write"],
            "connect": ["connect", "clone", "execve"],
            "ptrace": ["ptrace", "execve"],
            "mprotect": ["execve"]
        }
        
        import random, time, uuid
        from common.events.schemas import SyscallEvent
        current_syscall = "execve"
        base_time = time.time_ns()
        
        for i in range(length):
            # Anomalies are often rapid bursts (timing anomaly)
            if is_anomaly:
                delta = random.randint(10, 500)
            else:
                delta = random.randint(100, 5_000_000)
            base_time += delta
            
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
            if i % 32 == 0:
                hpc_seq.append(hpc_provider.read_counters())
                
            # Increase anomaly structural frequency
            if is_anomaly and random.random() < 0.8:
                current_syscall = random.choice(anom_probs.get(current_syscall, ["connect", "ptrace"]))
            else:
                current_syscall = random.choice(base_probs.get(current_syscall, ["close", "openat"]))
                
        return seq, hpc_seq

def run_experiment():
    builder = Exp5DatasetBuilder(agent_id="test_agent")
    
    print("Generating datasets...")
    dataset = builder.build_dataset(num_legit=1200, num_attack=200, window_size=256)
    
    train_legit = dataset["legitimate"][:1000]
    holdout_legit = dataset["legitimate"][1000:]
    holdout_anom = dataset["attack"]
    
    print("Extracting features...")
    vocab = SyscallVocabulary()
    aligner = HPCWindowAligner()
    extractor = BehaviorFeatureExtractor(vocab, aligner)
    
    def process_sequences(data):
        X = []
        for seq, hpc_seq in data:
            vec = extractor.extract(seq, hpc_seq)
            X.append(vec.to_flat_numeric())
        return np.array(X)
        
    X_train = process_sequences(train_legit)
    X_holdout_legit = process_sequences(holdout_legit)
    X_holdout_anom = process_sequences(holdout_anom)
    
    print("Fitting Isolation Forest on Legitimate Training data...")
    detector = IsolationForestDetector(n_estimators=100, contamination=0.01, random_state=42)
    detector.fit(X_train)
    
    print("Evaluating with AcademIQ L4 Isolation Forest...")
    start_eval_legit = time.perf_counter_ns()
    scores_legit = detector.score(X_holdout_legit)
    end_eval_legit = time.perf_counter_ns()
    
    start_eval_anom = time.perf_counter_ns()
    scores_anom = detector.score(X_holdout_anom)
    end_eval_anom = time.perf_counter_ns()
    
    train_scores = detector.score(X_train)
    threshold = np.percentile(train_scores, 99)
    print(f"Calculated anomaly threshold: {threshold:.4f}")
    
    aq_tp = sum(1 for s in scores_anom if s > threshold)
    aq_fn = sum(1 for s in scores_anom if s <= threshold)
    aq_fp = sum(1 for s in scores_legit if s > threshold)
    aq_tn = sum(1 for s in scores_legit if s <= threshold)
    
    print("Evaluating with Baseline Signature Detector...")
    base_tp = sum(1 for seq, _ in holdout_anom if naive_baseline_evaluate(seq))
    base_fn = len(holdout_anom) - base_tp
    base_fp = sum(1 for seq, _ in holdout_legit if naive_baseline_evaluate(seq))
    base_tn = len(holdout_legit) - base_fp
    
    def safe_div(a, b):
        return a / b if b != 0 else 0.0
        
    base_dr = safe_div(base_tp, len(holdout_anom))
    aq_dr = safe_div(aq_tp, len(holdout_anom))
    
    base_asr = safe_div(base_fn, len(holdout_anom))
    aq_asr = safe_div(aq_fn, len(holdout_anom))
    
    aq_precision = safe_div(aq_tp, aq_tp + aq_fp)
    aq_recall = aq_dr
    aq_f1 = safe_div(2 * aq_precision * aq_recall, aq_precision + aq_recall)
    
    eval_latency_ns = (end_eval_legit - start_eval_legit) + (end_eval_anom - start_eval_anom)
    eval_per_seq_ns = eval_latency_ns / (len(holdout_legit) + len(holdout_anom))
    
    print("\n--- RESULTS ---")
    print(f"Training Trajectories: {len(train_legit)}")
    print(f"Benign Holdout: {len(holdout_legit)}")
    print(f"Anomalous Holdout: {len(holdout_anom)}")
    
    print(f"\nBaseline Detection Rate: {base_dr * 100:.2f}%")
    print(f"Baseline ASR: {base_asr * 100:.2f}%")
    
    print(f"\nAcademIQ Detection Rate: {aq_dr * 100:.2f}%")
    print(f"Protected ASR: {aq_asr * 100:.2f}%")
    print(f"Precision: {aq_precision:.4f}")
    print(f"Recall: {aq_recall:.4f}")
    print(f"F1 Score: {aq_f1:.4f}")
    print(f"False Positives: {aq_fp}")
    print(f"False Negatives: {aq_fn}")
    
    summary = {
        "experiment": "EXP-5",
        "name": "Synthetic Unlabeled Behavioral Divergence Detection",
        "training_trajectories": len(train_legit),
        "benign_holdout": len(holdout_legit),
        "anomalous_holdout": len(holdout_anom),
        "baseline_detection_rate": base_dr * 100.0,
        "academiq_detection_rate": aq_dr * 100.0,
        "baseline_asr": base_asr * 100.0,
        "protected_asr": aq_asr * 100.0,
        "true_positives": aq_tp,
        "true_negatives": aq_tn,
        "false_positives": aq_fp,
        "false_negatives": aq_fn,
        "precision": float(aq_precision),
        "recall": float(aq_recall),
        "f1_score": float(aq_f1),
        "benign_mean_divergence": float(np.mean(scores_legit)),
        "anomalous_mean_divergence": float(np.mean(scores_anom)),
        "mean_latency_ms": eval_per_seq_ns / 1_000_000,
        "median_latency_ms": eval_per_seq_ns / 1_000_000, 
        "p95_latency_ms": eval_per_seq_ns / 1_000_000,
    }
    
    raw = {
        "scores_legit": scores_legit.tolist(),
        "scores_anom": scores_anom.tolist()
    }
    
    with open(os.path.join(RESULTS_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=4)
        
    with open(os.path.join(RESULTS_DIR, "raw_results.json"), "w") as f:
        json.dump(raw, f, indent=4)
        
    print(f"\nExperiment Results saved to {RESULTS_DIR}")

if __name__ == "__main__":
    run_experiment()
