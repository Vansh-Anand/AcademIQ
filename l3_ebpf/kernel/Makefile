CLANG ?= clang
LLVM_STRIP ?= llvm-strip
BPF_TARGET = bpf

# If vmlinux.h is not present locally, dump it from running kernel
# bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h

all: execve.bpf.o

execve.bpf.o: execve.bpf.c events.h
	$(CLANG) -g -O2 -target $(BPF_TARGET) -D__TARGET_ARCH_x86 -c $< -o $@
	$(LLVM_STRIP) -g $@

clean:
	rm -f *.bpf.o
