#!/bin/bash
# L3 Isolation Test Script
# Tests that unprivileged or containerized workloads cannot bypass L3 boundaries.

echo "========================================"
echo "AcademIQ eBPF Isolation Test"
echo "========================================"

# Requires root to use unshare, but then runs the test as nobody
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Run as root. The script will drop privileges automatically."
    exit 1
fi

echo "[1] Testing unprivileged access to /sys/kernel/debug/tracing..."
# Run as nobody
OUTPUT=$(su -s /bin/bash nobody -c "cat /sys/kernel/debug/tracing/trace 2>&1")
if [[ "$OUTPUT" == *"Permission denied"* ]]; then
    echo "[PASS] Unprivileged user denied access to debugfs tracing."
else
    echo "[FAIL] Unprivileged user accessed tracing: $OUTPUT"
fi

echo "[2] Testing unprivileged access to /sys/fs/bpf..."
OUTPUT=$(su -s /bin/bash nobody -c "ls /sys/fs/bpf 2>&1")
if [[ "$OUTPUT" == *"Permission denied"* ]] || [[ "$OUTPUT" == *"No such file"* ]]; then
    echo "[PASS] Unprivileged user denied access to bpffs."
else
    echo "[FAIL] Unprivileged user accessed bpffs: $OUTPUT"
fi

echo "[3] Testing unprivileged execution of bpftool..."
OUTPUT=$(su -s /bin/bash nobody -c "bpftool prog list 2>&1")
if [[ "$OUTPUT" == *"Permission denied"* ]] || [[ "$OUTPUT" == *"Error"* ]] || [[ "$OUTPUT" == *"not found"* ]]; then
    echo "[PASS] Unprivileged user denied execution/listing of BPF programs."
else
    echo "[FAIL] Unprivileged user executed bpftool: $OUTPUT"
fi

echo "========================================"
echo "Isolation Test Complete."
