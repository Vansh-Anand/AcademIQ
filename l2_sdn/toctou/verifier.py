import os
from typing import List, Tuple
from .identity import PathIdentity

class TOCTOUVerifier:
    def verify(self, identities: List[PathIdentity]) -> Tuple[bool, str]:
        """
        Verifies that the filesystem objects haven't changed identity.
        Called right before execution.
        """
        for identity in identities:
            if not os.path.exists(identity.resolved_path):
                return False, f"TOCTOU_OBJECT_REMOVED: {identity.path}"
                
            try:
                current_stat = os.stat(identity.resolved_path)
                if current_stat.st_ino != identity.inode_id or current_stat.st_dev != identity.device_id:
                    return False, f"TOCTOU_OBJECT_REPLACED: {identity.path}"
            except OSError:
                return False, f"TOCTOU_IDENTITY_UNAVAILABLE: {identity.path}"
                
        return True, "TOCTOU_VERIFIED"
