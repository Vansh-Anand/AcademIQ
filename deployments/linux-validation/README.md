# AcademIQ Native Linux Validation Environment

## Requirements
- Ubuntu 22.04+ or compatible Linux (Kernel >= 5.15, ideally 6.x).
- Root privileges (`CAP_SYS_ADMIN` and `CAP_BPF`).
- Mounted debugfs and bpffs.
- `clang`, `llvm`, and `libbpf` headers.

## Deployment Steps

### 1. Setup the Environment
On your native Linux target, clone the repository and navigate into it:
```bash
git clone https://github.com/your-org/AcademIQ.git
cd AcademIQ
```

Install system dependencies:
```bash
sudo apt-get update
sudo apt-get install -y clang llvm libbpf-dev linux-headers-$(uname -r) bpftool python3-pip python3-venv linux-tools-common linux-tools-generic
```

### 2. Python Virtual Environment
Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run Preflight Validation
Execute the preflight script to ensure your environment is fully capable of running L3 native eBPF:
```bash
sudo ./deployments/linux-validation/preflight.sh
```
Or use the CLI:
```bash
sudo python -m cli.main l3 doctor
```

All essential checks (BTF, Kernel, bpffs) should emit `[PASS]`.

### 4. Running Validation Tests
Once the environment passes preflight, execute the integration tests to confirm full pipeline functionality natively:
```bash
sudo python -m pytest tests/integration/ -v
```

### Note on Windows Hosts
Running this directly under Windows (or standard WSL2 without a custom-compiled kernel) is unsupported and will fail gracefully. Please use a native Linux instance for L3 validation.
