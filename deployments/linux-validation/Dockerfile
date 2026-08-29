FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    clang \
    llvm \
    libbpf-dev \
    linux-headers-generic \
    bpftool \
    python3 \
    python3-pip \
    linux-tools-common \
    linux-tools-generic \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/academiq

# Note: Running eBPF requires --privileged and -v /sys/kernel/debug:/sys/kernel/debug:rw
COPY . /opt/academiq/

RUN pip3 install --break-system-packages -r requirements.txt

CMD ["./deployments/linux-validation/run-benchmarks.sh"]
