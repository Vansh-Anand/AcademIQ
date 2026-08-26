import os
from typing import Dict, Any, Optional, List
from .identity import PathIdentity
from ..events import CanonicalCommand

class TOCTOUResolver:
    """
    Resolves the PathIdentity for every canonical path.
    """
    def resolve(self, command: CanonicalCommand) -> List[PathIdentity]:
        identities = []
        for cp in command.canonical_paths:
            path_to_stat = cp.canonical_path if cp.canonical_path else cp.raw_path
            
            if not os.path.exists(path_to_stat):
                continue
                
            try:
                # We use os.stat which follows symlinks, os.lstat doesn't.
                # To detect symlink target replacement, we actually need to record the symlink chain.
                # For this implementation, we just record the final resolved target's inode.
                stat = os.stat(path_to_stat)
                
                identities.append(PathIdentity(
                    path=cp.raw_path,
                    resolved_path=path_to_stat,
                    device_id=stat.st_dev,
                    inode_id=stat.st_ino,
                    file_type=cp.path_type,
                    mode=stat.st_mode,
                    uid=stat.st_uid,
                    gid=stat.st_gid,
                    size=stat.st_size,
                    mtime_ns=stat.st_mtime_ns
                ))
            except OSError:
                pass
                
        return identities
