import yaml
import os
from typing import Tuple
from ..events import CanonicalCommand

class CommandPolicyMatcher:
    def __init__(self, policy_path: str = "config/policies/shell.yaml"):
        try:
            with open(policy_path, "r") as f:
                self.policy = yaml.safe_load(f) or {}
        except Exception as e:
            # Fail closed
            raise RuntimeError(f"Could not load SDN policy from {policy_path}: {e}")
            
    def match(self, canon_ast: CanonicalCommand) -> Tuple[str, str]:
        """
        Evaluates the CanonicalCommand against the loaded policy.
        Returns (decision, reason). Decision is ALLOW, BLOCK, or REVIEW.
        """
        exe = canon_ast.executable
        exe_basename = os.path.basename(exe)
        if exe_basename.endswith(".exe"):
            exe_basename = exe_basename[:-4]
            
        allowed = self.policy.get("allowed_commands", [])
        blocked = self.policy.get("blocked_commands", [])
        
        # 1. Denylist check
        if exe_basename in blocked or exe in blocked:
            return "BLOCK", f"SDN_BLOCKED_COMMAND: {exe_basename}"
            
        # 2. Allowlist check
        if exe_basename not in allowed and exe not in allowed:
            return "BLOCK", f"SDN_POLICY_VIOLATION: Executable '{exe_basename}' not explicitly allowed."
            
        # 3. Path Restrictions
        restricted_paths = self.policy.get("restricted_paths", [])
        for cp in canon_ast.canonical_paths:
            path_str = cp.canonical_path.replace("\\", "/") if cp.canonical_path else cp.raw_path
            # Ignore Windows drive for test portability
            if ":" in path_str and path_str[1] == ":":
                path_str = path_str[2:]
                
            for rpath in restricted_paths:
                rpath_norm = rpath.replace("\\", "/")
                if ":" in rpath_norm and rpath_norm[1] == ":":
                    rpath_norm = rpath_norm[2:]
                
                # Check prefix/exact match
                if path_str.startswith(rpath_norm):
                    return "BLOCK", f"SDN_PATH_RESTRICTED: Access to '{rpath}' is restricted."
                    
        return "ALLOW", "SDN_ALLOWED"
