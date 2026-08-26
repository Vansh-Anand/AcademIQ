import os
from typing import Dict, Any, List
from .interfaces import NormalizationPass

class PathNormalizer(NormalizationPass):
    """
    Syntactically normalizes paths in arguments by resolving redundant
    separators, up-level references (..), and current-dir references (.).
    Does NOT resolve symlinks or check absolute identity (that's for Canonicalization).
    """
    def apply(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        normalized_args = []
        for arg in ast["arguments"]:
            # If the argument looks like a path (contains slashes), normalize it
            # We normalize all arguments just in case, as normpath on non-paths is mostly a no-op
            # but we must be careful with flags like --config=path
            
            # Simple heuristic: if it contains a slash, try to normalize
            if "/" in arg or "\\" in arg:
                # Need to handle --flag=value cases
                if "=" in arg:
                    key, val = arg.split("=", 1)
                    if "/" in val or "\\" in val:
                        # normalize the path part
                        val = os.path.normpath(val)
                        # Ensure forward slashes for cross-platform consistency in AST
                        val = val.replace("\\", "/") 
                        arg = f"{key}={val}"
                else:
                    arg = os.path.normpath(arg)
                    arg = arg.replace("\\", "/")
            normalized_args.append(arg)
            
        ast["arguments"] = normalized_args
        return ast

class BaseNormalizerChain:
    """
    Runs a series of normalization passes.
    Note: Whitespace and quoting are inherently normalized by ShlexCommandParser.
    """
    def __init__(self, passes: List[NormalizationPass]):
        self.passes = passes
        
    def normalize(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        current_ast = ast
        for p in self.passes:
            current_ast = p.apply(current_ast)
        return current_ast

def get_default_normalizer() -> BaseNormalizerChain:
    return BaseNormalizerChain([
        PathNormalizer()
    ])
