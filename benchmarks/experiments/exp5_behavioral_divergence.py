import os
import sys
import json
import time
import numpy as np
import torch
import torch.nn.functional as F
import yaml

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from l4_divergence.dataset.loader import DatasetBuilder
from l4_divergence.features.vocabulary import SyscallVocabulary
from l4_divergence.features.extractor import BehaviorFeatureExtractor
from l4_divergence.hpc.aligner import HPCWindowAligner
from l4_divergence.isolation_forest.detector import IsolationForestDetector
from l4_divergence.siamese.model import SiameseRecurrentAutoencoder
from l4_divergence.ensemble.divergence import DivergenceEnsemble, ScoreCalibrator

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "exp5")
os.makedirs(RESULTS_DIR, exist_ok=True)

def naive_baseline_evaluate(seq):
    syscall_names = [e.syscall_name for e in seq]
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
                
            if is_anomaly and random.random() < 0.8:
                current_syscall = random.choice(anom_probs.get(current_syscall, ["connect", "ptrace"]))
            else:
                current_syscall = random.choice(base_probs.get(current_syscall, ["close", "openat"]))
                
        return seq, hpc_seq

def get_siamese_scores(model, centroid, seq_tensors, num_tensors):
    model.eval()
    scores = []
    with torch.no_grad():
        for seq, num in zip(seq_tensors, num_tensors):
            # Shape to (1, seq_len) and (1, num_features)
            t_seq = torch.tensor([seq], dtype=torch.long)
            t_num = torch.tensor([num], dtype=torch.float32)
            encoded = model.encode(t_seq, t_num)
            dist = F.pairwise_distance(encoded, centroid, p=2).item()
            scores.append(dist)
    return np.array(scores)

def compute_metrics(legit_scores, anom_scores, threshold):
    tp = sum(1 for s in anom_scores if s > threshold)
    fn = sum(1 for s in anom_scores if s <= threshold)
    fp = sum(1 for s in legit_scores if s > threshold)
    tn = sum(1 for s in legit_scores if s <= threshold)
    
    dr = tp / len(anom_scores) if len(anom_scores) > 0 else 0.0
    asr = fn / len(anom_scores) if len(anom_scores) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = dr
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / len(legit_scores) if len(legit_scores) > 0 else 0.0
    
    return {
        "detection_rate": dr * 100,
        "asr": asr * 100,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": fpr * 100,
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn
    }

def run_experiment():
    # 1. Configuration
    policy_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "policies", "divergence.yaml")
    with open(policy_path, 'r') as f:
        config = yaml.safe_load(f)
    
    ensemble_cfg = config.get("drift_detection", {}).get("ensemble", {})
    if not ensemble_cfg.get("enabled", False):
        print("Ensemble not enabled in config. Exiting.")
        return
        
    s_weight = ensemble_cfg.get("siamese_weight", 0.5)
    i_weight = ensemble_cfg.get("isolation_weight", 0.5)
    
    # 2. Dataset Generation
    builder = Exp5DatasetBuilder(agent_id="test_agent")
    print("Generating datasets...")
    np.random.seed(42)
    dataset = builder.build_dataset(num_legit=1200, num_attack=200, window_size=256)
    
    train_legit = dataset["legitimate"][:1000]
    holdout_legit = dataset["legitimate"][1000:]
    holdout_anom = dataset["attack"]
    
    print("Extracting features...")
    vocab = SyscallVocabulary()
    aligner = HPCWindowAligner()
    extractor = BehaviorFeatureExtractor(vocab, aligner)
    
    def extract_features(data):
        X_flat = []
        X_seq = []
        X_num = []
        for seq, hpc_seq in data:
            vec = extractor.extract(seq, hpc_seq)
            X_flat.append(vec.to_flat_numeric())
            X_seq.append(vec.sequence_features)
            X_num.append(vec.to_flat_numeric())
        return np.array(X_flat), X_seq, X_num
        
    X_train_flat, tr_seq, tr_num = extract_features(train_legit)
    X_hl_flat, hl_seq, hl_num = extract_features(holdout_legit)
    X_ha_flat, ha_seq, ha_num = extract_features(holdout_anom)
    
    # 3. Isolation Forest
    print("Fitting Isolation Forest...")
    detector = IsolationForestDetector(n_estimators=100, contamination=0.01, random_state=42)
    detector.fit(X_train_flat)
    
    start_eval_iso = time.perf_counter_ns()
    if_scores_hl = detector.score(X_hl_flat)
    if_scores_ha = detector.score(X_ha_flat)
    end_eval_iso = time.perf_counter_ns()
    
    # 4. Siamese Network
    ckpt_path = os.path.join(os.path.dirname(__file__), "..", "..", ensemble_cfg.get("siamese_checkpoint"))
    cent_path = os.path.join(os.path.dirname(__file__), "..", "..", ensemble_cfg.get("centroid_path"))
    
    if not os.path.exists(ckpt_path):
        print("Siamese checkpoint missing! Training now...")
        from l4_divergence.siamese.train import train_siamese_model
        train_siamese_model(seed=42)
        
    print("Loading Siamese Network...")
    siam_model = SiameseRecurrentAutoencoder(vocab_size=vocab.size(), num_numeric_features=len(tr_num[0]))
    siam_model.load_state_dict(torch.load(ckpt_path, weights_only=True))
    siam_centroid = torch.load(cent_path, weights_only=True)
    
    start_eval_siam = time.perf_counter_ns()
    siam_scores_hl = get_siamese_scores(siam_model, siam_centroid, hl_seq, hl_num)
    siam_scores_ha = get_siamese_scores(siam_model, siam_centroid, ha_seq, ha_num)
    end_eval_siam = time.perf_counter_ns()
    
    # 5. Ensemble Integration
    ensemble = DivergenceEnsemble(siamese_weight=s_weight, isolation_weight=i_weight)
    
    # Calibrate on train legit and holdout anomaly to establish full scale
    # Normally we'd use a dedicated validation set, but this simulates finding bounds.
    if_scores_tr = detector.score(X_train_flat)
    siam_scores_tr = get_siamese_scores(siam_model, siam_centroid, tr_seq, tr_num)
    
    combined_if = np.concatenate([if_scores_tr, if_scores_ha])
    combined_siam = np.concatenate([siam_scores_tr, siam_scores_ha])
    ensemble.calibrator.fit(combined_siam.tolist(), combined_if.tolist())
    
    ens_scores_hl = []
    ens_components_hl = []
    for ss, iso in zip(siam_scores_hl, if_scores_hl):
        res = ensemble.evaluate(ss, iso)
        ens_scores_hl.append(res["score"])
        ens_components_hl.append(res)
        
    ens_scores_ha = []
    ens_components_ha = []
    for ss, iso in zip(siam_scores_ha, if_scores_ha):
        res = ensemble.evaluate(ss, iso)
        ens_scores_ha.append(res["score"])
        ens_components_ha.append(res)
        
    # Calculate thresholds for individual models and ensemble
    # Threshold = 99th percentile of legitimate holdout or training
    th_if = np.percentile(if_scores_tr, 99)
    th_siam = np.percentile(siam_scores_tr, 99)
    th_ens = np.percentile([ensemble.evaluate(s, i)["score"] for s, i in zip(siam_scores_tr, if_scores_tr)], 99)
    
    # 6. Metrics Calculation
    print("Evaluating Baseline Signature Detector...")
    base_tp = sum(1 for seq, _ in holdout_anom if naive_baseline_evaluate(seq))
    base_fn = len(holdout_anom) - base_tp
    base_fp = sum(1 for seq, _ in holdout_legit if naive_baseline_evaluate(seq))
    base_tn = len(holdout_legit) - base_fp
    base_dr = (base_tp / len(holdout_anom)) * 100
    base_asr = (base_fn / len(holdout_anom)) * 100
    
    metrics_if = compute_metrics(if_scores_hl, if_scores_ha, th_if)
    metrics_siam = compute_metrics(siam_scores_hl, siam_scores_ha, th_siam)
    metrics_ens = compute_metrics(ens_scores_hl, ens_scores_ha, th_ens)
    
    # Contribution Analysis
    hl_if_comp = np.mean([c["isolation_component"] for c in ens_components_hl])
    hl_siam_comp = np.mean([c["siamese_component"] for c in ens_components_hl])
    hl_ens_mean = np.mean(ens_scores_hl)
    
    ha_if_comp = np.mean([c["isolation_component"] for c in ens_components_ha])
    ha_siam_comp = np.mean([c["siamese_component"] for c in ens_components_ha])
    ha_ens_mean = np.mean(ens_scores_ha)
    
    # Latency
    latency_ns = (end_eval_iso - start_eval_iso) + (end_eval_siam - start_eval_siam)
    total_samples = len(holdout_legit) + len(holdout_anom)
    mean_latency_ms = (latency_ns / total_samples) / 1_000_000
    
    print("\n--- RESULTS ---")
    print(f"Training Trajectories: {len(train_legit)}")
    print(f"Benign Holdout: {len(holdout_legit)}")
    print(f"Anomalous Holdout: {len(holdout_anom)}")
    
    print(f"\nBaseline Signature: DR={base_dr:.2f}%, ASR={base_asr:.2f}%")
    print(f"Isolation Forest:   DR={metrics_if['detection_rate']:.2f}%, ASR={metrics_if['asr']:.2f}%, F1={metrics_if['f1']:.4f}")
    print(f"Siamese Model:      DR={metrics_siam['detection_rate']:.2f}%, ASR={metrics_siam['asr']:.2f}%, F1={metrics_siam['f1']:.4f}")
    print(f"Ensemble:           DR={metrics_ens['detection_rate']:.2f}%, ASR={metrics_ens['asr']:.2f}%, F1={metrics_ens['f1']:.4f}")
    
    print("\n--- SOFT-VOTE CONTRIBUTION ANALYSIS ---")
    print(f"Configured Weights -> IF: {i_weight}, Siamese: {s_weight}")
    print(f"Benign Average Components   -> IF: {hl_if_comp:.4f}, Siamese: {hl_siam_comp:.4f} => Final: {hl_ens_mean:.4f}")
    print(f"Anomalous Average Component -> IF: {ha_if_comp:.4f}, Siamese: {ha_siam_comp:.4f} => Final: {ha_ens_mean:.4f}")
    
    summary = {
        "experiment_id": "EXP-5",
        "timestamp": time.time(),
        "random_seed": 42,
        "dataset": {
            "training_trajectories": len(train_legit),
            "benign_holdout": len(holdout_legit),
            "anomalous_holdout": len(holdout_anom)
        },
        "model_architecture": "SiameseRecurrentAutoencoder + IsolationForest",
        "baseline_metrics": {
            "detection_rate": base_dr,
            "asr": base_asr,
            "tp": base_tp, "fn": base_fn, "fp": base_fp, "tn": base_tn
        },
        "isolation_forest_metrics": metrics_if,
        "neural_metrics": metrics_siam,
        "ensemble_metrics": metrics_ens,
        "ensemble_weights": {
            "isolation": i_weight,
            "siamese": s_weight
        },
        "score_normalization": "Min-Max bounds scaled to [0,1]",
        "soft_vote_analysis": {
            "benign_mean_if_component": float(hl_if_comp),
            "benign_mean_siamese_component": float(hl_siam_comp),
            "benign_mean_final": float(hl_ens_mean),
            "anomalous_mean_if_component": float(ha_if_comp),
            "anomalous_mean_siamese_component": float(ha_siam_comp),
            "anomalous_mean_final": float(ha_ens_mean)
        },
        "mean_latency_ms": mean_latency_ms,
        "environment_metadata": {
            "python_version": sys.version,
            "torch_version": torch.__version__
        }
    }
    
    with open(os.path.join(RESULTS_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=4)
        
    print(f"\nExperiment Results saved to {RESULTS_DIR}")

if __name__ == "__main__":
    run_experiment()
