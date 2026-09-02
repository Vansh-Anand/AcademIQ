import os
import shutil
import hashlib
from typing import Dict, Any, List
from .events import NormalizedCommand, CanonicalCommand, CommandPath, SingleCanonicalCommand

class CommandCanonicalizer:
    """
    Transforms a normalized AST into a canonical representation.
    Resolves exact executable path and absolute paths for arguments.
    (Pass 5 of the normalizer pipeline)
    """
    def canonicalize(self, ast: NormalizedCommand) -> CanonicalCommand:
        parsed = ast.normalized_ast
        
        canonical_commands = []
        texts = []
        
        for cmd in parsed.commands:
            executable = cmd.executable
            
            # 1. Resolve Executable
            resolved_exe = shutil.which(executable)
            canonical_exe = resolved_exe if resolved_exe else executable
            canonical_exe = canonical_exe.replace("\\", "/")
            
            # 2. Resolve Arguments and Paths
            canonical_args = []
            canonical_paths = []
            
            for idx, arg in enumerate(cmd.arguments):
                val = arg.resolved_value or arg.raw_value
                
                is_path = False
                resolved_path = None
                
                # Heuristic for paths
                if "/" in val or "\\" in val or os.path.exists(val):
                    if "=" in val:
                        key, path_part = val.split("=", 1)
                        if "/" in path_part or "\\" in path_part or os.path.exists(path_part):
                            resolved_path = os.path.realpath(os.path.abspath(path_part)).replace("\\", "/")
                            canonical_args.append(f"{key}={resolved_path}")
                            is_path = True
                        else:
                            canonical_args.append(val)
                    else:
                        resolved_path = os.path.realpath(os.path.abspath(val)).replace("\\", "/")
                        canonical_args.append(resolved_path)
                        is_path = True
                else:
                    canonical_args.append(val)
                    
                if is_path and resolved_path:
                    path_type = "UNKNOWN"
                    if os.path.exists(resolved_path):
                        path_type = "DIRECTORY" if os.path.isdir(resolved_path) else "FILE"
                    
                    canonical_paths.append(CommandPath(
                        raw_path=val,
                        canonical_path=resolved_path,
                        path_type=path_type,
                        source_argument_index=idx
                    ))
                    
            canonical_text = f"{canonical_exe} " + " ".join(canonical_args)
            texts.append(canonical_text)
            
            canonical_commands.append(SingleCanonicalCommand(
                executable=canonical_exe,
                canonical_arguments=canonical_args,
                canonical_paths=canonical_paths,
                canonical_environment={},
                canonical_redirections=cmd.redirections,
                canonical_text=canonical_text
            ))
            
        full_canonical_text = " ; ".join(texts)
        command_hash = hashlib.sha256(full_canonical_text.encode()).hexdigest()
        
        return CanonicalCommand(
            commands=canonical_commands,
            canonical_text=full_canonical_text,
            command_hash=command_hash
        )
