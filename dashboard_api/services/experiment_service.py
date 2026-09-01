import os
import json
from typing import List, Dict, Any, Optional

from dashboard_api.schemas.experiments import ExperimentItem, ExperimentDetail, ExperimentAggregate, ExperimentSummaryAll
from dashboard_api.schemas.common import ExecutionMode

class ExperimentService:
    def __init__(self, results_dir: str = "benchmarks/results"):
        self.results_dir = results_dir

    def get_experiments(self) -> List[ExperimentItem]:
        if not os.path.exists(self.results_dir):
            return []
            
        experiments = []
        for d in os.listdir(self.results_dir):
            dir_path = os.path.join(self.results_dir, d)
            if os.path.isdir(dir_path):
                summary_path = os.path.join(dir_path, "summary.json")
                raw_path = os.path.join(dir_path, "raw_results.json")
                
                exp_id = d
                name_parts = exp_id.replace("_", " ").title()
                
                exp = ExperimentItem(
                    id=exp_id,
                    name=name_parts,
                    result_available=os.path.exists(summary_path),
                    summary_path=summary_path if os.path.exists(summary_path) else None,
                    raw_results_available=os.path.exists(raw_path)
                )
                experiments.append(exp)
        
        experiments.sort(key=lambda x: x.id)
        return experiments

    def get_experiment(self, exp_id: str) -> Optional[ExperimentDetail]:
        dir_path = os.path.join(self.results_dir, exp_id)
        summary_path = os.path.join(dir_path, "summary.json")
        
        if not os.path.exists(summary_path):
            return None
            
        with open(summary_path, "r") as f:
            data = json.load(f)
            
        # Determine execution type
        execution_type = ExecutionMode.BENCHMARK
        if "synthetic" in exp_id.lower() or "simulated" in exp_id.lower():
            execution_type = ExecutionMode.SYNTHETIC
        elif "real_llm" in exp_id or "cross_model" in exp_id:
            execution_type = ExecutionMode.REAL_RUNTIME
            
        # Extract metrics safely
        if isinstance(data, list):
            metrics = data
            performance = {}
            sample_size = len(data)
            timestamp = None
        else:
            metrics = data.get("Metrics") or data.get("Prevention") or data
            performance = data.get("Performance") or {}
            
            # Sample size and timestamp
            sample_size = data.get("sample_size") or data.get("Metadata", {}).get("total_samples")
            timestamp = data.get("timestamp") or data.get("Metadata", {}).get("timestamp")
            
        if timestamp is not None:
            timestamp = str(timestamp)

        
        artifact_paths = [summary_path]
        raw_path = os.path.join(dir_path, "raw_results.json")
        if os.path.exists(raw_path):
            artifact_paths.append(raw_path)
            
        return ExperimentDetail(
            experiment_id=exp_id,
            title=exp_id.replace("_", " ").title(),
            execution_type=execution_type,
            sample_size=sample_size,
            metrics=metrics,
            latency_metrics=performance,
            limitations="Native execution not validated. Tests performed in Windows simulation.",
            artifact_paths=artifact_paths,
            timestamp=timestamp
        )

    def get_summary_all(self) -> ExperimentSummaryAll:
        experiments = []
        for exp in self.get_experiments():
            if exp.result_available:
                detail = self.get_experiment(exp.id)
                if not detail:
                    continue
                    
                metrics = detail.metrics
                
                if not isinstance(metrics, dict):
                    continue
                
                detection_rate = metrics.get("overall_detection_rate") or metrics.get("detection_rate") or metrics.get("prevention_rate")
                asr = metrics.get("overall_asr") or metrics.get("asr")
                
                lat_metrics = detail.latency_metrics
                latency_ms = None
                if lat_metrics:
                    latency_ns = lat_metrics.get("mean_pipeline_latency_ns") or lat_metrics.get("mean_latency_ns") or lat_metrics.get("mean_append_ns")
                    if latency_ns:
                        latency_ms = latency_ns / 1_000_000.0
                    
                agg = ExperimentAggregate(
                    id=exp.id,
                    detection_rate=detection_rate,
                    asr=asr,
                    latency_ms=latency_ms,
                    execution_type=detail.execution_type
                )
                experiments.append(agg)
                
        return ExperimentSummaryAll(experiments=experiments)
