#!/bin/bash
set -e

echo "========================================="
echo " AcademIQ Phase 4 eBPF Setup (Linux)"
echo "========================================="

if [ "$EUID" -ne 0 ]; then
  echo "[!] Please run as root (or use sudo) to install eBPF tools."
  exit 1
fi

echo "[+] Checking for required dependencies..."
if ! command -v clang &> /dev/null; then
    echo "[-] clang not found. Installing..."
    apt-get update && apt-get install -y clang llvm
fi

if ! command -v bpftool &> /dev/null; then
    echo "[-] bpftool not found. Installing..."
    apt-get install -y linux-tools-common linux-tools-generic linux-tools-$(uname -r)
fi

echo "[+] Dependencies satisfied."

KERNEL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../l3_ebpf/kernel" && pwd)"
echo "[+] Compiling eBPF Kernel probes in $KERNEL_DIR"

cd "$KERNEL_DIR"

if [ ! -f "vmlinux.h" ]; then
    echo "[+] Dumping vmlinux.h for local kernel..."
    bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h
fi

make clean
make

echo "[+] Compilation successful."
echo "    Object generated: $KERNEL_DIR/execve.bpf.o"
echo ""
echo "[INFO] AcademIQ Phase 4 eBPF is ready for Linux execution."
