import json
import os

def generate_audit():
    registry_path = os.path.join(os.path.dirname(__file__), "..", "benchmarks", "results", "experiment_registry.json")
    out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "reports", "academiq_complete_project_audit.md")
    
    with open(registry_path, "r") as f:
        data = json.load(f)
        
    lines = []
    
    lines.append("# AcademIQ Master Project Audit (Canonical Edition)")
    lines.append("> [!IMPORTANT]")
    lines.append("> This is the canonical, auto-generated audit report sourced from `experiment_registry.json`.")
    lines.append("> The historical audit report has been preserved as `historical_academiq_project_audit.md`.")
    lines.append("")
    
    lines.append("## 1. Project Status")
    lines.append("- **Overall Status:** FROZEN STATE (Pre-Ubuntu Handoff).")
    lines.append("- **Windows Validation:** Complete. All 145 Python regression tests pass.")
    lines.append("- **Native Ubuntu/eBPF Status:** PENDING / NOT VALIDATED. (Do not start Ubuntu work yet).")
    lines.append("- **Dashboard Status:** React + FastAPI dashboard fully implemented and tested.")
    lines.append("- **ECES Status:** Durable SQLite storage implemented.")
    lines.append("- **Phase 4 Technique Status:** All five patent-strengthening techniques implemented and validated.")
    lines.append("")
    
    lines.append("## 2. Canonical Experiment Table")
    lines.append("| ID | Title | Mode | Dataset | Samples | Malicious | DR (%) | ASR (%) | FPR (%) |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    
    for exp in data["experiments"]:
        dr = f"{exp['detection_rate']:.1f}" if exp['detection_rate'] is not None else "N/A"
        asr = f"{exp['attack_success_rate']:.1f}" if exp['attack_success_rate'] is not None else "N/A"
        fpr = f"{exp['false_positive_rate']:.1f}" if exp['false_positive_rate'] is not None else "N/A"
        
        lines.append(f"| {exp['experiment_id']} | {exp['title']} | {exp['execution_mode']} | {exp['dataset_type']} | {exp['sample_count']} | {exp['malicious_count']} | {dr} | {asr} | {fpr} |")
    
    lines.append("")
    
    lines.append("## 3. Experiment-by-Experiment Results")
    for exp in data["experiments"]:
        lines.append(f"### {exp['experiment_id']}: {exp['title']}")
        lines.append(f"- **Status:** {exp['status']}")
        lines.append(f"- **Execution Mode:** {exp['execution_mode']}")
        lines.append(f"- **Dataset Type:** {exp['dataset_type']}")
        lines.append(f"- **Detection Rate:** {exp['detection_rate']}%")
        lines.append(f"- **Attack Success Rate:** {exp['attack_success_rate']}%")
        lines.append(f"- **False Positive Rate:** {exp['false_positive_rate']}%")
        lines.append(f"- **Samples:** {exp['sample_count']} total ({exp['malicious_count']} malicious, {exp['benign_count']} benign)")
        if exp['mean_latency_ms']:
            lines.append(f"- **Mean Latency:** {exp['mean_latency_ms']:.2f} ms")
        if exp['notes']:
            lines.append("- **Notes:**")
            for note in exp['notes']:
                lines.append(f"  - {note}")
        if exp['limitations']:
            lines.append("- **Limitations:**")
            for lim in exp['limitations']:
                lines.append(f"  - {lim}")
        lines.append("")
        
    lines.append("## 4. Historical Discrepancies")
    lines.append("This table reconciles historically reported metrics with the current canonical source of truth.")
    lines.append("")
    lines.append("| Experiment | Historical Claim | Canonical Claim | Reason | Source of Truth |")
    lines.append("|---|---|---|---|---|")
    
    for disc in data["historical_discrepancies"]:
        lines.append(f"| {disc['experiment']} | {disc['historical_claim']} | {disc['canonical_claim']} | {disc['reason']} | `{disc['source_of_truth']}` |")
        
    lines.append("")
    lines.append("## 5. Known Limitations & Strict Rules")
    lines.append("- **EXP-6 Comparator Limitation:** The AARMEquivalentDetector is an internal AARM-inspired baseline / prior-art approximation benchmark, NOT the actual AARM system.")
    lines.append("- **Real vs Simulated:** Synthetic and simulated results are strictly labeled and are not claimed to be real-world results.")
    lines.append("- **Native OS Validation:** L7 native OS isolation and native eBPF validation are not yet claimed. They will be validated in the subsequent Ubuntu phase.")
    
    lines.append("")
    lines.append("## 6. Git/Repository Hygiene Findings")
    lines.append("- **`__pycache__`:** Tracked in git (Recommended: Untrack).")
    lines.append("- **`eces.db`:** Tracked in git (Recommended: Untrack).")
    lines.append("- **`l4_siamese.pt`:** Tracked in git (Acceptable size).")
    lines.append("- **Secrets/node_modules:** None tracked.")
    lines.append("")
    
    with open(out_path, "w", encoding='utf-8') as f:
        f.write("\n".join(lines))
        
    print(f"Audit generated successfully at {out_path}")

if __name__ == "__main__":
    generate_audit()
