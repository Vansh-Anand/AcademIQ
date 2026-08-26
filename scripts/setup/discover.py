import platform
import subprocess
import sys
import os

def check_command(command: list[str]) -> bool:
    try:
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def discover_environment():
    print("============================================================")
    print("ACADEMIQ ENVIRONMENT DISCOVERY")
    print("============================================================")
    
    # OS & Architecture
    print(f"OS: {platform.system()} {platform.release()} ({platform.version()})")
    print(f"Architecture: {platform.machine()}")
    print(f"Python: {platform.python_version()}")
    
    # Dependencies
    has_docker = check_command(["docker", "--version"])
    print(f"Docker: {'AVAILABLE' if has_docker else 'UNAVAILABLE'}")
    
    has_clang = check_command(["clang", "--version"])
    print(f"Clang: {'AVAILABLE' if has_clang else 'UNAVAILABLE'}")
    
    # eBPF / Kernel (Basic check if on Linux)
    if platform.system() == "Linux":
        print("Kernel: AVAILABLE")
        has_bpftool = check_command(["bpftool", "version"])
        print(f"bpftool: {'AVAILABLE' if has_bpftool else 'UNAVAILABLE'}")
        has_perf = check_command(["perf", "--version"])
        print(f"perf_event: {'AVAILABLE' if has_perf else 'UNAVAILABLE'}")
    else:
        print("Kernel: REQUIRES_LINUX")
        print("eBPF Support: UNAVAILABLE")
        print("perf_event: UNAVAILABLE")
    
    # TPM
    if platform.system() == "Linux":
        has_tpm = check_command(["tpm2_pcrread"])
        print(f"TPM (tpm2-tools): {'AVAILABLE' if has_tpm else 'UNAVAILABLE'}")
    elif platform.system() == "Windows":
        # Check using PowerShell (Requires privileges usually, but simple check)
        try:
            res = subprocess.run(["powershell", "-Command", "(Get-Tpm).TpmPresent"], capture_output=True, text=True)
            has_tpm = "True" in res.stdout
            print(f"TPM (Windows): {'AVAILABLE' if has_tpm else 'UNAVAILABLE'}")
        except:
            print("TPM: NOT_TESTED")
    else:
        print("TPM: NOT_TESTED")
        
    print("TEE Capability: NOT_TESTED")
    print("GPU/CUDA: NOT_TESTED")
    print("Ollama: " + ("AVAILABLE" if check_command(["ollama", "--version"]) else "UNAVAILABLE"))
    
    print("============================================================")
    print("Warning: Simulation mode is highly recommended for this host.")

if __name__ == "__main__":
    discover_environment()
