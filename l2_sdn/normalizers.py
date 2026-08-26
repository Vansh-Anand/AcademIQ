from typing import Dict, Any, List, Optional
import re
import base64
import urllib.parse
from .events import ParsedCommand, NormalizedCommand, CommandArgument

class NormalizationPass:
    def apply(self, ast: ParsedCommand) -> ParsedCommand:
        raise NotImplementedError

class SafeEnvironmentSnapshot:
    def __init__(self, allowed_vars: Dict[str, str]):
        self.vars = allowed_vars

class VariableExpansionPass(NormalizationPass):
    def __init__(self, env: SafeEnvironmentSnapshot):
        self.env = env
        
    def apply(self, ast: ParsedCommand) -> ParsedCommand:
        new_args = []
        for arg in ast.arguments:
            val = arg.raw_value
            if arg.is_variable:
                # Naive regex for $VAR and ${VAR}
                # Replace known variables
                def repl(match):
                    var_name = match.group(1) or match.group(2)
                    return self.env.vars.get(var_name, match.group(0)) # preserve if unknown
                    
                val = re.sub(r'\$\{([a-zA-Z0-9_]+)\}|\$([a-zA-Z0-9_]+)', repl, val)
                
            new_args.append(CommandArgument(
                raw_value=val,
                resolved_value=val,
                is_path=arg.is_path,
                is_substitution=arg.is_substitution,
                is_variable=arg.is_variable
            ))
        return ParsedCommand(
            executable=ast.executable,
            arguments=new_args,
            redirections=ast.redirections,
            pipelines=ast.pipelines,
            command_substitutions=ast.command_substitutions,
            environment_references=ast.environment_references,
            aliases=ast.aliases,
            source_location=ast.source_location
        )

class EncodingDecodePass(NormalizationPass):
    def apply(self, ast: ParsedCommand) -> ParsedCommand:
        new_args = []
        for arg in ast.arguments:
            val = arg.resolved_value or arg.raw_value
            
            # Base64 heuristic decode
            if len(val) >= 4 and len(val) % 4 == 0 and re.match(r'^[A-Za-z0-9+/]+={0,2}$', val):
                try:
                    decoded = base64.b64decode(val).decode('utf-8')
                    # only keep it if it's printable to avoid decoding random binary
                    if decoded.isprintable():
                        val = decoded
                except Exception:
                    pass
                    
            # URL Decode
            if "%" in val:
                val = urllib.parse.unquote(val)
                
            new_args.append(CommandArgument(
                raw_value=arg.raw_value,
                resolved_value=val,
                is_path=arg.is_path,
                is_substitution=arg.is_substitution,
                is_variable=arg.is_variable
            ))
            
        return ParsedCommand(
            executable=ast.executable,
            arguments=new_args,
            redirections=ast.redirections,
            pipelines=ast.pipelines,
            command_substitutions=ast.command_substitutions,
            environment_references=ast.environment_references,
            aliases=ast.aliases,
            source_location=ast.source_location
        )

class ANSICQuotingPass(NormalizationPass):
    def apply(self, ast: ParsedCommand) -> ParsedCommand:
        new_args = []
        for arg in ast.arguments:
            val = arg.resolved_value or arg.raw_value
            # Extremely basic ANSI-C and hex resolution for demonstration
            # bashlex handles most quotes automatically, but we might get literal \x6d
            if "\\x" in val:
                def hex_repl(match):
                    try:
                        return chr(int(match.group(1), 16))
                    except ValueError:
                        return match.group(0)
                val = re.sub(r'\\x([0-9a-fA-F]{2})', hex_repl, val)
                
            # Octal resolution \155
            if "\\" in val and re.search(r'\\[0-7]{3}', val):
                def octal_repl(match):
                    try:
                        return chr(int(match.group(1), 8))
                    except ValueError:
                        return match.group(0)
                val = re.sub(r'\\([0-7]{3})', octal_repl, val)
                
            new_args.append(CommandArgument(
                raw_value=arg.raw_value,
                resolved_value=val,
                is_path=arg.is_path,
                is_substitution=arg.is_substitution,
                is_variable=arg.is_variable
            ))
            
        # We must also normalize the executable name
        exe = ast.executable
        if "\\x" in exe:
            exe = re.sub(r'\\x([0-9a-fA-F]{2})', lambda m: chr(int(m.group(1), 16)), exe)
        if "\\" in exe and re.search(r'\\[0-7]{3}', exe):
            exe = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m.group(1), 8)), exe)
            
        return ParsedCommand(
            executable=exe,
            arguments=new_args,
            redirections=ast.redirections,
            pipelines=ast.pipelines,
            command_substitutions=ast.command_substitutions,
            environment_references=ast.environment_references,
            aliases=ast.aliases,
            source_location=ast.source_location
        )

class AliasResolutionPass(NormalizationPass):
    def __init__(self, aliases: Dict[str, str]):
        self.aliases = aliases
        
    def apply(self, ast: ParsedCommand) -> ParsedCommand:
        exe = ast.executable
        if exe in self.aliases:
            # For this simple prototype, if it's an alias, just replace the executable name.
            # A real shell alias replaces the whole command line and re-parses it.
            alias_cmd = self.aliases[exe]
            parts = alias_cmd.split(" ")
            new_exe = parts[0]
            new_args = []
            
            for p in parts[1:]:
                new_args.append(CommandArgument(raw_value=p, resolved_value=p))
                
            new_args.extend(ast.arguments)
            
            return ParsedCommand(
                executable=new_exe,
                arguments=new_args,
                redirections=ast.redirections,
                pipelines=ast.pipelines,
                command_substitutions=ast.command_substitutions,
                environment_references=ast.environment_references,
                aliases=ast.aliases + [exe],
                source_location=ast.source_location
            )
            
        return ast

class BaseNormalizerChain:
    def __init__(self, passes: List[NormalizationPass]):
        self.passes = passes
        
    def normalize(self, ast: ParsedCommand) -> NormalizedCommand:
        current_ast = ast
        transformations = []
        for p in self.passes:
            current_ast = p.apply(current_ast)
            transformations.append({"pass": p.__class__.__name__})
            
        import hashlib
        # Hash computation placeholder
        
        return NormalizedCommand(
            original_hash="mockhash",
            normalized_text=f"{current_ast.executable} " + " ".join([a.resolved_value or a.raw_value for a in current_ast.arguments]),
            normalized_ast=current_ast,
            transformations_applied=transformations
        )

def get_default_normalizer() -> BaseNormalizerChain:
    return BaseNormalizerChain([
        VariableExpansionPass(SafeEnvironmentSnapshot({"HOME": "/root", "USER": "root"})),
        EncodingDecodePass(),
        ANSICQuotingPass(),
        AliasResolutionPass({"ll": "ls -la"})
    ])
