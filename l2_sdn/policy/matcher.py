import yaml
import os
from typing import Dict, Any, List, Tuple

class SemanticPolicyMatcher:
    def __init__(self, policy_path: str):
        try:
            with open(policy_path, "r") as f:
                self.policy = yaml.safe_load(f) or {}
        except Exception as e:
            # Fail closed on missing policy
            raise RuntimeError(f"Could not load SDN policy from {policy_path}: {e}")
            
    def match(self, ast: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Evaluates the canonical AST against the loaded policy.
        Returns (is_allowed, reason).
        """
        # 1. Executable check (we check the basename since canonicalizer resolves absolute path)
        exe = ast["executable"]
        exe_basename = os.path.basename(exe)
        # Handle Windows .exe extension
        if exe_basename.endswith(".exe"):
            exe_basename = exe_basename[:-4]
            
        allowed_exes = self.policy.get("allowed_executables", [])
        if exe_basename not in allowed_exes and exe not in allowed_exes:
            return False, f"Executable '{exe}' is not in allowed list."
            
        # 2. Syntax flags check
        flags = ast.get("flags", {})
        if flags.get("has_pipeline") and not self.policy.get("allow_pipelines", False):
            return False, "Pipelines are forbidden by policy."
        if flags.get("has_redirection") and not self.policy.get("allow_redirection", False):
            return False, "Redirections are forbidden by policy."
            
        # 3. Argument checks
        forbidden_args = self.policy.get("forbidden_arguments", [])
        forbidden_dirs = self.policy.get("forbidden_directories", [])
        
        for arg in ast["arguments"]:
            if arg in forbidden_args:
                return False, f"Forbidden argument detected: '{arg}'"
                
            # Path containment check for forbidden directories
            # Since ast arguments are canonicalized (absolute), we can check prefix
            arg_norm = arg.replace("\\", "/")
            # Remove drive letter for cross-platform checking
            if ":" in arg_norm and arg_norm[1] == ":":
                arg_norm = arg_norm[2:]
                
            for fdir in forbidden_dirs:
                fdir_norm = fdir.replace("\\", "/")
                if ":" in fdir_norm and fdir_norm[1] == ":":
                    fdir_norm = fdir_norm[2:]
                    
                # Simple prefix check
                if arg_norm.startswith(fdir_norm):
                    return False, f"Argument '{arg}' accesses forbidden directory '{fdir}'."
                    
        return True, "Passed all SDN semantic checks."
