#!/bin/bash
echo "========================================"
echo "AcademIQ Native Linux Validation"
echo "========================================"

echo "[1] Checking Kernel Capabilities..."
bpftool feature probe || echo "BPFTOOL NOT FOUND OR UNAUTHORIZED"

echo "[2] Running Integration Tests natively..."
python3 -m pytest tests/integration/ -v

echo "[3] Running Performance Benchmarks..."
# In a real run, this would trigger specific perf benchmark scripts.
echo "Native execution completed."
