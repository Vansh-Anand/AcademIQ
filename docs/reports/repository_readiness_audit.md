# Repository Readiness Audit

**Status:** Completed
**Scope:** Read-only Git tracked file hygiene scan.

## 1. SAFE TO COMMIT
- **Benchmark Results (`benchmarks/results/**/*.json`):** 34 JSON result files are intentionally versioned. These act as the immutable historical record of the Windows execution phase and should remain in Git.
- **Source Code (`*.py`, `*.ts`, `*.tsx`, etc.):** Core pipeline components are clean.
- **Frontend Source (`frontend/src`):** Clean.

## 2. SHOULD IGNORE (Untrack / Add to .gitignore)
- **`__pycache__` Directories:** Found 145 `.pyc` files actively tracked by Git. These should be removed from the index (`git rm -r --cached __pycache__`) and globally gitignored.
- **Temporary Execution Artifacts:** 
  - `benchmarks/results/technique4/temp/test_policy.yaml` is tracked. Temporary dynamic artifacts should be ignored.
- **`frontend/node_modules/`:** Not currently tracked (which is correct), but should ensure `.gitignore` covers it.

## 3. REVIEW REQUIRED
- **SQLite Databases:**
  - `.data/evidence/eces.db`
  - `benchmarks/results/phase_d_eces/eces_benchmark.db`
  - *Recommendation:* Live runtime databases and test evidence stores should generally not be tracked. If they serve as required test fixtures, they should be renamed to `.db.fixture` and dynamically copied during tests.
- **Large Model Binaries:**
  - `config/checkpoints/l4_siamese.pt`
  - `config/checkpoints/l4_benign_centroid.pt`
  - *Recommendation:* While small neural networks are acceptable for a self-contained test suite, ensure these remain under 100MB to avoid GitHub LFS requirements. They are currently small enough and are intentionally committed to support the offline zero-day ensemble.

## 4. No Secrets / Node Modules Found in Git
- No `.env`, API keys, or `node_modules` were found actively tracked in the index.

**Note:** No automatic deletions were performed during this audit.
