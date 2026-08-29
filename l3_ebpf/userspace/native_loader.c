#include <stdio.h>
#include <stdlib.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include <unistd.h>
#include <sys/resource.h>
#include "../kernel/events.h"

// Define a handle structure to hold our objects
struct native_ebpf_handle {
    struct bpf_object *obj;
    struct bpf_link *link;
    struct ring_buffer *rb;
};

// Python callback signature
typedef void (*event_cb)(const struct syscall_event_t *event, int size);

static event_cb global_callback = NULL;

static int handle_event(void *ctx, void *data, size_t data_sz) {
    if (global_callback) {
        global_callback((const struct syscall_event_t *)data, (int)data_sz);
    }
    return 0;
}

// Exported C function to initialize and load the BPF program
struct native_ebpf_handle *init_bpf(const char *obj_file) {
    struct native_ebpf_handle *h = malloc(sizeof(*h));
    if (!h) return NULL;

    h->obj = NULL;
    h->link = NULL;
    h->rb = NULL;

    // Bump RLIMIT_MEMLOCK to allow BPF map creation
    struct rlimit rlim = {RLIM_INFINITY, RLIM_INFINITY};
    setrlimit(RLIMIT_MEMLOCK, &rlim);

    h->obj = bpf_object__open_file(obj_file, NULL);
    if (libbpf_get_error(h->obj)) {
        fprintf(stderr, "ERROR: opening BPF object file failed\n");
        free(h);
        return NULL;
    }

    if (bpf_object__load(h->obj)) {
        fprintf(stderr, "ERROR: loading BPF object file failed\n");
        bpf_object__close(h->obj);
        free(h);
        return NULL;
    }

    struct bpf_program *prog = bpf_object__find_program_by_name(h->obj, "tracepoint__syscalls__sys_enter_execve");
    if (!prog) {
        fprintf(stderr, "ERROR: finding a prog in obj file failed\n");
        bpf_object__close(h->obj);
        free(h);
        return NULL;
    }

    h->link = bpf_program__attach(prog);
    if (libbpf_get_error(h->link)) {
        fprintf(stderr, "ERROR: bpf_program__attach failed\n");
        bpf_object__close(h->obj);
        free(h);
        return NULL;
    }

    return h;
}

// Exported C function to start the ring buffer
int start_ringbuffer(struct native_ebpf_handle *h, event_cb callback) {
    if (!h || !h->obj) return -1;
    global_callback = callback;

    int map_fd = bpf_object__find_map_fd_by_name(h->obj, "rb");
    if (map_fd < 0) {
        fprintf(stderr, "ERROR: finding a map in obj file failed\n");
        return -1;
    }

    h->rb = ring_buffer__new(map_fd, handle_event, NULL, NULL);
    if (!h->rb) {
        fprintf(stderr, "ERROR: creating ring buffer failed\n");
        return -1;
    }
    return 0;
}

// Exported C function to poll the ring buffer
int poll_ringbuffer(struct native_ebpf_handle *h, int timeout_ms) {
    if (!h || !h->rb) return -1;
    return ring_buffer__poll(h->rb, timeout_ms);
}

// Exported C function to cleanup
void cleanup_bpf(struct native_ebpf_handle *h) {
    if (!h) return;
    if (h->rb) ring_buffer__free(h->rb);
    if (h->link) bpf_link__destroy(h->link);
    if (h->obj) bpf_object__close(h->obj);
    free(h);
}
