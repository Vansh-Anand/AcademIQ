# Forensic Audit Session: Changes and Outputs

This document serves as a record of all code changes, commands, and outputs executed during the final forensic reconciliation session.

## 1. Test Isolation Patch

**File Modified:** `tests/benchmarks/test_exp3_real_llm.py`
**Change Made:** Added a mock patch to prevent the test from overwriting the canonical results of EXP-3 Real LLM.

```python
@pytest.mark.skipif(os.environ.get("CI") == "true", reason="Heavy model test skipped in CI")
def test_full_pipeline_mock(tmp_path):
    import unittest.mock as mock
    from benchmarks.experiments.exp3_real_llm_exfiltration import run_evaluation
    
    with mock.patch('benchmarks.experiments.exp3_real_llm_exfiltration.RESULTS_DIR', str(tmp_path)):
        mock_gens = [
            # ... mock generations ...
        ]
        
        run_evaluation(mock_gens)
        
        summary_file = os.path.join(str(tmp_path), "summary.json")
        assert os.path.exists(summary_file)
        with open(summary_file, "r") as f:
            summary = json.load(f)
            
        assert summary["dataset_processing"]["unique_total"] == 2
        assert summary["llm_l5_riskchain"]["DR"] == 100.0 # Caught the mock full chain
```

**Test Execution Output:**
```text
============================= test session starts =============================
platform win32 -- Python 3.13.6, pytest-8.2.2, pluggy-1.6.0
rootdir: C:\Users\VANSH ANAND\Desktop\AcademIQ
plugins: anyio-4.14.2, Faker-25.9.1, hypothesis-6.165.10, langsmith-0.8.15, asyncio-0.23.7, cov-5.0.0, httpx-0.30.0
asyncio: mode=Mode.STRICT
collected 8 items

tests\benchmarks\test_exp3_real_llm.py ........                          [100%]

============================== 8 passed in 5.38s ==============================
```

## 2. Canonical Registry Creation

**Files Created:**
- `benchmarks/results/experiment_registry.json`
- `tests/benchmarks/validate_registry.py`

**Validation Execution Output:**
```text
Validating EXP-1...
Validating EXP-2A...
Validating EXP-2B...
Validating EXP-3...
Validating EXP-3_REAL_LLM...
Validating EXP-4...
Validating EXP-5...
Validating EXP-6...
Experiment registry is valid.
```

## 3. Git Repository Hygiene

**Changes Made:**
- Updated `.gitignore` to explicitly include `__pycache__/`, `*.pyc`, and `.data/evidence/eces.db`.
- Untracked all dynamically generated cache and database files from the git index using `git rm --cached`.

**Execution Output (Excerpt):**
```text
rm 'cli/__pycache__/l4_cli.cpython-313.pyc'
rm 'cli/__pycache__/l5_cli.cpython-313.pyc'
rm 'cli/__pycache__/main.cpython-313.pyc'
rm 'common/events/__pycache__/base.cpython-313.pyc'
rm 'common/events/__pycache__/schemas.cpython-313.pyc'
...
rm 'tests/benchmarks/__pycache__/test_exp6_aarm_comparison.cpython-313-pytest-8.2.2.pyc'
rm 'tests/benchmarks/__pycache__/test_experiment_harness.cpython-313-pytest-8.2.2.pyc'
...
rm 'tests/unit/__pycache__/test_gcd.cpython-313-pytest-8.2.2.pyc'
rm 'tests/unit/__pycache__/test_l2.cpython-313-pytest-8.2.2.pyc'
```

## 4. Final Regression Suite Run

**Command:** `python -m pytest tests/`

**Execution Output:**
```text
============================= test session starts =============================
platform win32 -- Python 3.13.6, pytest-8.2.2, pluggy-1.6.0
rootdir: C:\Users\VANSH ANAND\Desktop\AcademIQ
plugins: anyio-4.14.2, Faker-25.9.1, hypothesis-6.165.10, langsmith-0.8.15, asyncio-0.23.7, cov-5.0.0, httpx-0.30.0
asyncio: mode=Mode.STRICT
collected 146 items

tests\benchmarks\test_exp1.py ...s                                       [  2%]
tests\benchmarks\test_exp1_cross_model.py ....                           [  5%]
tests\benchmarks\test_exp2.py ....                                       [  8%]
tests\benchmarks\test_exp2_real_llm.py .........                         [ 14%]
tests\benchmarks\test_exp3.py ...                                        [ 16%]
tests\benchmarks\test_exp3_real_llm.py ........                          [ 21%]
tests\benchmarks\test_exp4.py ..                                         [ 23%]
tests\benchmarks\test_exp5.py ....                                       [ 26%]
tests\benchmarks\test_exp6_aarm_comparison.py ..                         [ 27%]
tests\benchmarks\test_experiment_harness.py ..                           [ 28%]
tests\benchmarks\test_phase_d_eces_durability.py .....                   [ 32%]
tests\benchmarks\test_technique1_cusum_drift.py .....                    [ 35%]
tests\benchmarks\test_technique2_maxflow_riskchain.py ...                [ 37%]
tests\benchmarks\test_technique3_cross_session_replay.py .........       [ 43%]
tests\benchmarks\test_technique4_gcd_hot_reload.py ....                  [ 46%]
tests\benchmarks\test_technique5_cross_layer_synergy.py ..               [ 47%]
tests\benchmarks\test_telemetry_replay.py .                              [ 48%]
tests\dashboard_api\test_contract.py .........                           [ 54%]
tests\dashboard_api\test_evidence.py ....                                [ 57%]
tests\dashboard_api\test_experiments.py ...                              [ 59%]
tests\dashboard_api\test_health.py .                                     [ 60%]
tests\dashboard_api\test_integration.py ..                               [ 61%]
tests\dashboard_api\test_pipeline.py ...                                 [ 63%]
tests\dashboard_api\test_status.py ......                                [ 67%]
tests\integration\test_l2_adversarial.py ....................            [ 81%]
tests\integration\test_l3_ebpf.py .                                      [ 82%]
tests\integration\test_l4_divergence.py ....                             [ 84%]
tests\integration\test_l5_riskchain.py .....                             [ 88%]
tests\integration\test_l6_eces.py ....                                   [ 91%]
tests\integration\test_l7_trust.py .....                                 [ 94%]
tests\unit\test_events.py ..                                             [ 95%]
tests\unit\test_gcd.py ..                                                [ 97%]
tests\unit\test_l2.py ....                                               [100%]

================== 145 passed, 1 skipped in 86.94s (0:01:26) ==================
```

## 5. Audit Auto-Generation

**Files Created/Modified:**
- `tools/generate_project_audit.py`
- `docs/reports/academiq_complete_project_audit.md` (Newly generated)
- `docs/reports/historical_academiq_project_audit.md` (Preserved original)

**Command:** `python tools/generate_project_audit.py`

**Execution Output:**
```text
Audit generated successfully at C:\Users\VANSH ANAND\Desktop\AcademIQ\tools\..\docs\reports\academiq_complete_project_audit.md
```
