#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>
#include <bpf/bpf_tracing.h>
#include "events.h"

// Ring buffer for sending events to userspace
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024); // 256 KB
} rb SEC(".maps");

// Map to filter allowed cgroups
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, u64); // cgroup_id
    __type(value, u8); // allowed flag
} cgroup_filter SEC(".maps");

SEC("tracepoint/syscalls/sys_enter_execve")
int tracepoint__syscalls__sys_enter_execve(struct trace_event_raw_sys_enter *ctx)
{
    u64 id = bpf_get_current_pid_tgid();
    u32 pid = id >> 32;
    u32 tid = (u32)id;
    
    u64 cgroup_id = bpf_get_current_cgroup_id();
    
    // Check if this cgroup is monitored
    u8 *monitored = bpf_map_lookup_elem(&cgroup_filter, &cgroup_id);
    if (!monitored) {
        return 0;
    }

    struct syscall_event_t *e;
    e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
    if (!e) {
        return 0; // Drop event
    }

    e->type = EVENT_EXECVE;
    e->timestamp_ns = bpf_ktime_get_ns();
    e->pid = pid;
    e->tid = tid;
    e->cgroup_id = cgroup_id;
    e->uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    e->gid = bpf_get_current_uid_gid() >> 32;

    bpf_get_current_comm(&e->comm, sizeof(e->comm));
    
    // Read the executable filename (first arg of execve)
    const char *filename_ptr = (const char *)ctx->args[0];
    bpf_probe_read_user_str(&e->executable, sizeof(e->executable), filename_ptr);
    
    // We would also read argv array here into arg_payload
    // Simplification for prototype
    e->arg_payload[0] = '\0';

    bpf_ringbuf_submit(e, 0);
    return 0;
}

char _license[] SEC("license") = "GPL";
