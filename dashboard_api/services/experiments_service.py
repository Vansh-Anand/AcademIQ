import os
import json
from typing import List, Dict, Any, Optional
from dashboard_api.schemas.experiments import ExperimentNormalized, ExperimentSummary
from dashboard_api.schemas.pipeline import ExecutionMode

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "benchmarks", "results")

class ExperimentService:
    @classmethod
    def get_all_experiments(cls) -> List[ExperimentSummary]:
        experiments = []
        if not os.path.exists(RESULTS_DIR):
            return experiments
            
        for d in os.listdir(RESULTS_DIR):
            if os.path.isdir(os.path.join(RESULTS_DIR, d)):
                summary_file = os.path.join(RESULTS_DIR, d, "summary.json")
                if os.path.exists(summary_file):
                    exp_norm = cls._normalize_experiment(d, summary_file)
                    if exp_norm:
                        # Extract primary metric safely
                        primary_metric = None
                        if exp_norm.attack_success_rate is not None:
                            primary_metric = {"name": "Protected ASR", "value": exp_norm.attack_success_rate, "suffix": "%"}
                        elif exp_norm.f1_score is not None:
                            primary_metric = {"name": "F1 Score", "value": exp_norm.f1_score, "suffix": ""}
                        elif exp_norm.false_positive_rate is not None:
                            primary_metric = {"name": "FPR", "value": exp_norm.false_positive_rate, "suffix": "%"}
                            
                        experiments.append(ExperimentSummary(
                            experiment_id=exp_norm.experiment_id,
                            title=exp_norm.title,
                            category=exp_norm.category,
                            description=exp_norm.description,
                            execution_mode=exp_norm.execution_mode,
                            model_name=exp_norm.model_name,
                            primary_metric=primary_metric
                        ))
        
        # Sort by experiment ID for consistent ordering
        experiments.sort(key=lambda x: x.experiment_id)
        return experiments

    @classmethod
    def get_experiment(cls, experiment_id: str) -> Optional[ExperimentNormalized]:
        if not os.path.exists(RESULTS_DIR):
            return None
            
        for d in os.listdir(RESULTS_DIR):
            if os.path.isdir(os.path.join(RESULTS_DIR, d)):
                summary_file = os.path.join(RESULTS_DIR, d, "summary.json")
                if os.path.exists(summary_file):
                    exp_norm = cls._normalize_experiment(d, summary_file)
                    if exp_norm and exp_norm.experiment_id.upper() == experiment_id.upper():
                        return exp_norm
                        
        return None

    @classmethod
    def _normalize_experiment(cls, dir_name: str, summary_file: str) -> Optional[ExperimentNormalized]:
        try:
            with open(summary_file, "r") as f:
                raw_data = json.load(f)
        except Exception:
            return None
            
        if isinstance(raw_data, list):
            raw_data = {"items": raw_data}
            
        # Default initialization
        title = dir_name.replace("_", " ").title()
        description = f"Results for {dir_name}"
        category = "Core Security Experiments"
        execution_mode = ExecutionMode.BENCHMARK
        model_name = raw_data.get("model", raw_data.get("model_used")) if isinstance(raw_data, dict) else None
        sample_size = raw_data.get("total_trials", raw_data.get("dataset_processing", {}).get("raw_total")) if isinstance(raw_data, dict) else None
        
        if not sample_size and "dataset" in raw_data:
            dataset = raw_data["dataset"]
            sample_size = sum(v for k, v in dataset.items() if isinstance(v, (int, float)))
            
        if "real_llm" in dir_name or "cross_model" in dir_name or "model" in raw_data:
            execution_mode = ExecutionMode.REAL_RUNTIME
            if "exp" in dir_name:
                category = "Real LLM Validation"
        elif "technique" in dir_name:
            category = "Adaptive / Patent Techniques"
        
        experiment_id = raw_data.get("experiment_id", dir_name.upper())
        
        # Extract metrics based on schema
        baseline_metrics = raw_data.get("baseline", raw_data.get("baseline_metrics", raw_data.get("synthetic_baseline", raw_data.get("raw_l3_only"))))
        protected_metrics = raw_data.get("protected", raw_data.get("ensemble_metrics", raw_data.get("llm_l5_riskchain", raw_data.get("sdn_normalized_l3"))))
        
        detection_rate = raw_data.get("detection_rate")
        attack_success_rate = raw_data.get("attack_success_rate", raw_data.get("asr"))
        false_positive_rate = raw_data.get("false_positive_rate", raw_data.get("fpr"))
        precision = raw_data.get("precision")
        recall = raw_data.get("recall")
        f1_score = raw_data.get("f1_score", raw_data.get("f1"))
        
        # Try to infer from protected_metrics if not top level
        if protected_metrics:
            if detection_rate is None:
                detection_rate = protected_metrics.get("detection_rate", protected_metrics.get("DR"))
            if attack_success_rate is None:
                attack_success_rate = protected_metrics.get("asr", protected_metrics.get("ASR"))
            if false_positive_rate is None:
                false_positive_rate = protected_metrics.get("fpr", protected_metrics.get("FPR", protected_metrics.get("false_positive_rate")))
            if precision is None:
                precision = protected_metrics.get("precision", protected_metrics.get("Precision"))
            if recall is None:
                recall = protected_metrics.get("recall", protected_metrics.get("Recall"))
            if f1_score is None:
                f1_score = protected_metrics.get("f1", protected_metrics.get("F1"))
        
        # Special case for EXP-1
        if "prevention_rate" in raw_data:
            detection_rate = raw_data.get("prevention_rate")
            if attack_success_rate is None and protected_metrics:
                attack_success_rate = protected_metrics.get("ASR")
                
        # Special case for technique1
        if "recalibration_successful" in raw_data:
            title = "CUSUM Adaptive ECE Recalibration"
            description = "Analyzes dynamic drift threshold adjustments under simulated adversarial conditions."
            execution_mode = ExecutionMode.SIMULATED
            
        # Special case for technique 5
        if dir_name == "technique5":
            false_positive_rate = protected_metrics.get("false_positive_rate") if protected_metrics else None

        # Special case for EXP-6
        if dir_name == "exp6_aarm_comparison":
            overall = raw_data.get("overall_metrics", {})
            academiq_stats = overall.get("AcademIQ", {})
            attack_success_rate = academiq_stats.get("ASR")
            detection_rate = academiq_stats.get("DR")
            false_positive_rate = academiq_stats.get("FPR")
            f1_score = academiq_stats.get("F1")
            
            # Re-structure for UI visualization
            raw_data["protected_metrics"] = academiq_stats
            raw_data["baseline_metrics"] = overall.get("AARM", {})

        # Build latencies
        latency_metrics = None
        if "mean_latency_ms" in raw_data:
            latency_metrics = {
                "mean": raw_data.get("mean_latency_ms"),
                "median": raw_data.get("median_latency_ms"),
                "p95": raw_data.get("p95_latency_ms")
            }
        elif "latencies_ms" in raw_data:
            latency_metrics = raw_data.get("latencies_ms")
        elif "latency" in raw_data and "normalized" in raw_data["latency"]:
            latency_metrics = raw_data["latency"]["normalized"]

        limitations = raw_data.get("limitations", raw_data.get("known_limitations", []))
        if not limitations and execution_mode == ExecutionMode.SIMULATED:
            limitations.append("Simulation environment does not perfectly model OS jitter.")
        if not limitations and category == "Synthetic Dataset Experiment":
            limitations.append("Synthetic datasets may not capture real-world zero-day distributions fully.")
            
        # Human readable mapping for known experiments
        known_titles = {
            "EXP-1": "Direct Prompt Injection Prevention",
            "EXP-2": "Obfuscated Shell Command Detection",
            "EXP-3": "Multi-Step Exfiltration Chain Detection",
            "EXP-4": "Ptrace Privilege Escalation Behavior",
            "EXP-5": "Behavioral Divergence Zero-Day Detection",
            "EXP-2_REAL_LLM": "Real LLM L2 Obfuscated Shell Eval",
            "EXP-3_REAL_LLM": "Real LLM L5 Causal Chain Eval",
        }
        
        if experiment_id in known_titles:
            title = known_titles[experiment_id]
        
        # Omit phase_d_eces as it's an infrastructure validation, not a core security benchmark metric visualization
        if dir_name == "phase_d_eces":
            return None

        return ExperimentNormalized(
            experiment_id=experiment_id,
            title=title,
            category=category,
            description=description,
            execution_mode=execution_mode,
            model_name=model_name,
            sample_size=sample_size,
            baseline_metrics=baseline_metrics,
            protected_metrics=protected_metrics,
            detection_rate=detection_rate,
            attack_success_rate=attack_success_rate,
            false_positive_rate=false_positive_rate,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            latency_metrics=latency_metrics,
            key_findings=None,
            known_limitations=limitations if limitations else None,
            raw_artifact=raw_data
        )
