import os
from typing import Dict, Any, Optional, Tuple

class TOCTOUResolver:
    """
    Mitigates Time-of-Check to Time-of-Use (TOCTOU) races.
    
    PLATFORM LIMITATION (Windows):
    On Linux, we could use O_PATH or directory file descriptors (openat).
    On Windows, we rely on checking file identity (st_ino, st_dev) before use.
    If the file identity changes between L2 validation and execution, the 
    execution layer must abort.
    """
    def __init__(self):
        self.inode_cache: Dict[str, Tuple[int, int]] = {}
        
    def resolve_and_lock(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a canonical AST. For every path argument, stats it and records the inode.
        Returns the AST enriched with TOCTOU metadata.
        """
        # Create a deep copy to enrich
        enriched_ast = {
            "executable": ast["executable"],
            "arguments": list(ast["arguments"]),
            "flags": dict(ast["flags"]),
            "toctou_locks": {}
        }
        
        # 1. Lock the executable (if it's an absolute path that exists)
        exe = enriched_ast["executable"]
        if os.path.exists(exe):
            stat = os.stat(exe)
            enriched_ast["toctou_locks"][exe] = (stat.st_ino, stat.st_dev)
            
        # 2. Lock arguments
        for arg in enriched_ast["arguments"]:
            # If it's a key=value pair
            if "=" in arg:
                _, val = arg.split("=", 1)
                if os.path.exists(val):
                    stat = os.stat(val)
                    enriched_ast["toctou_locks"][val] = (stat.st_ino, stat.st_dev)
            elif os.path.exists(arg):
                stat = os.stat(arg)
                enriched_ast["toctou_locks"][arg] = (stat.st_ino, stat.st_dev)
                
        return enriched_ast

    def verify_locks(self, toctou_locks: Dict[str, Tuple[int, int]]) -> bool:
        """
        Called right before execution to ensure no underlying files changed identity.
        """
        for path, (expected_ino, expected_dev) in toctou_locks.items():
            if not os.path.exists(path):
                return False # File deleted/moved
            current_stat = os.stat(path)
            if current_stat.st_ino != expected_ino or current_stat.st_dev != expected_dev:
                return False # File replaced (TOCTOU race detected)
        return True
