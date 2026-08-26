import os
import shutil
from typing import Dict, Any
from .interfaces import CommandCanonicalizer

class ASTCanonicalizer(CommandCanonicalizer):
    """
    Transforms a normalized AST into a canonical representation.
    This resolves the exact executable path and absolute paths for arguments.
    """
    def canonicalize(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        executable = ast["executable"]
        
        # 1. Resolve Executable
        # If it's a built-in or not found, which returns None. We keep original if None.
        resolved_exe = shutil.which(executable)
        canonical_exe = resolved_exe if resolved_exe else executable
        # Ensure forward slashes for cross-platform consistency
        canonical_exe = canonical_exe.replace("\\", "/")
        
        # 2. Resolve Arguments
        canonical_args = []
        for arg in ast["arguments"]:
            # Check if argument is likely a path that exists
            # For security, we might want to canonicalize ANYTHING that looks like a path
            # But resolving non-paths can corrupt data.
            # Strategy: if os.path.exists or it has slash, we try to realpath it.
            
            if "/" in arg or "\\" in arg:
                if "=" in arg:
                    key, val = arg.split("=", 1)
                    if "/" in val or "\\" in val:
                        # try to resolve absolute path (handles symlinks on Linux, reparse points on Windows to some degree)
                        val = os.path.realpath(os.path.abspath(val))
                        val = val.replace("\\", "/")
                        arg = f"{key}={val}"
                else:
                    arg = os.path.realpath(os.path.abspath(arg))
                    arg = arg.replace("\\", "/")
            
            canonical_args.append(arg)
            
        return {
            "executable": canonical_exe,
            "arguments": canonical_args,
            "flags": ast["flags"]
        }
