import shlex
from typing import Dict, Any
from .interfaces import CommandParser

class ShlexCommandParser(CommandParser):
    def parse(self, command: str) -> Dict[str, Any]:
        """
        Parses a shell command into a structured AST-like dictionary.
        Uses shlex to securely handle POSIX quoting and escaping.
        """
        try:
            # We use posix=True to properly handle quotes and escapes
            tokens = shlex.split(command, posix=True)
        except ValueError as e:
            # shlex raises ValueError on unclosed quotes
            raise ValueError(f"Failed to parse shell command: {e}")
            
        if not tokens:
            return {"executable": "", "arguments": []}
            
        executable = tokens[0]
        arguments = tokens[1:]
        
        # In a more advanced implementation, we would also detect pipelines (|),
        # redirections (>, <), and command substitutions. 
        # For this prototype, we'll extract the executable and arguments.
        # We will flag if we see suspicious shell characters that shlex tokenized.
        
        has_pipeline = "|" in tokens
        has_redirection = ">" in tokens or "<" in tokens or ">>" in tokens
        has_logic = "&&" in tokens or "||" in tokens or ";" in tokens
        
        ast = {
            "executable": executable,
            "arguments": arguments,
            "flags": {
                "has_pipeline": has_pipeline,
                "has_redirection": has_redirection,
                "has_logic": has_logic
            }
        }
        
        return ast
