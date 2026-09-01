# AcademIQ Reproduction Guide

This guide provides the authoritative, verified commands to reproduce the AcademIQ environment, execute tests, and launch the application.

## Python Backend Setup

```bash
# Ensure Python 3.13 is installed, then create and activate a virtual environment (Windows)
python -m venv venv
.\venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

## Running the Dashboard

```bash
# 1. Start the FastAPI backend
uvicorn dashboard_api.main:app --reload --port 8000

# 2. In a separate terminal, start the React frontend
cd frontend
npm install
npm run dev
```

## Testing

```bash
# Run the complete Python regression suite
python -m pytest tests/ -v

# Run the frontend unit tests
cd frontend
npm run test

# Validate the frontend build
cd frontend
npm run build
```

## Experiments & Benchmarks

The benchmark suite includes the core EXPs and patent strengthening techniques. 
Heavy LLM evaluations will automatically download the `TinyLlama` model if not present.

```bash
# EXP-1: Direct Prompt Injection
python benchmarks/experiments/exp1_direct_prompt_injection.py

# EXP-2: Obfuscated Shell Command
python benchmarks/experiments/exp2_obfuscated_command.py

# Technique 1: CUSUM Drift Detection
python benchmarks/experiments/technique1_cusum_drift.py
```

## ECES Chain Verification

To independently verify the cryptographically sealed ECES SQLite database offline:

```bash
python -m l6_eces.verify_chain --database .data/evidence/eces.db
```
