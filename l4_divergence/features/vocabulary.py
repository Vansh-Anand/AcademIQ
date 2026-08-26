class SyscallVocabulary:
    """Standardized vocabulary for system calls across environments."""
    
    CATEGORIES = {
        "execve": "EXEC",
        "execveat": "EXEC",
        "open": "OPEN",
        "openat": "OPEN",
        "openat2": "OPEN",
        "read": "READ",
        "pread64": "READ",
        "readv": "READ",
        "write": "WRITE",
        "pwrite64": "WRITE",
        "writev": "WRITE",
        "close": "CLOSE",
        "connect": "CONNECT",
        "socket": "SOCKET",
        "clone": "CLONE",
        "clone3": "CLONE",
        "ptrace": "PTRACE",
        "mmap": "MMAP",
        "mprotect": "MPROTECT",
        "dup": "DUP",
        "dup2": "DUP2",
        "dup3": "DUP2",
        "pipe": "PIPE",
        "pipe2": "PIPE",
        "fork": "FORK",
        "vfork": "FORK",
    }
    
    def __init__(self):
        # Build unique indices for the categories
        self._categories = sorted(list(set(self.CATEGORIES.values()))) + ["OTHER"]
        self._name_to_idx = {name: idx for idx, name in enumerate(self._categories)}
        self._idx_to_name = {idx: name for name, idx in self._name_to_idx.items()}
        
    def encode(self, syscall_name: str) -> int:
        cat = self.CATEGORIES.get(syscall_name, "OTHER")
        return self._name_to_idx[cat]
        
    def decode(self, idx: int) -> str:
        return self._idx_to_name.get(idx, "OTHER")
        
    def size(self) -> int:
        return len(self._categories)
        
    def version(self) -> str:
        return "1.0"
