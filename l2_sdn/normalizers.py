from typing import Dict, Any, List, Optional
import re
import base64
import urllib.parse
from .events import ParsedCommand, NormalizedCommand, CommandArgument, SingleCommand

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
        new_commands = []
        for cmd in ast.commands:
            new_args = []
            for arg in cmd.arguments:
                val = arg.raw_value
                if arg.is_variable:
                    def repl(match):
                        var_name = match.group(1) or match.group(2)
                        return self.env.vars.get(var_name, match.group(0))
                    val = re.sub(r'\$\{([a-zA-Z0-9_]+)\}|\$([a-zA-Z0-9_]+)', repl, val)
                    
                new_args.append(CommandArgument(
                    raw_value=val,
                    resolved_value=val,
                    is_path=arg.is_path,
                    is_substitution=arg.is_substitution,
                    is_variable=arg.is_variable
                ))
            new_commands.append(SingleCommand(
                executable=cmd.executable,
                arguments=new_args,
                redirections=cmd.redirections,
                pipelines=cmd.pipelines,
                command_substitutions=cmd.command_substitutions,
                environment_references=cmd.environment_references,
                aliases=cmd.aliases,
                source_location=cmd.source_location
            ))
        return ParsedCommand(commands=new_commands)

class EncodingDecodePass(NormalizationPass):
    def apply(self, ast: ParsedCommand) -> ParsedCommand:
        new_commands = []
        for cmd in ast.commands:
            new_args = []
            for arg in cmd.arguments:
                val = arg.resolved_value or arg.raw_value
                
                if len(val) >= 4 and len(val) % 4 == 0 and re.match(r'^[A-Za-z0-9+/]+={0,2}$', val):
                    try:
                        decoded = base64.b64decode(val).decode('utf-8')
                        if decoded.isprintable():
                            val = decoded
                    except Exception:
                        pass
                        
                if "%" in val:
                    val = urllib.parse.unquote(val)
                    
                new_args.append(CommandArgument(
                    raw_value=arg.raw_value,
                    resolved_value=val,
                    is_path=arg.is_path,
                    is_substitution=arg.is_substitution,
                    is_variable=arg.is_variable
                ))
            new_commands.append(SingleCommand(
                executable=cmd.executable,
                arguments=new_args,
                redirections=cmd.redirections,
                pipelines=cmd.pipelines,
                command_substitutions=cmd.command_substitutions,
                environment_references=cmd.environment_references,
                aliases=cmd.aliases,
                source_location=cmd.source_location
            ))
        return ParsedCommand(commands=new_commands)

class ANSICQuotingPass(NormalizationPass):
    def apply(self, ast: ParsedCommand) -> ParsedCommand:
        new_commands = []
        for cmd in ast.commands:
            new_args = []
            for arg in cmd.arguments:
                val = arg.resolved_value or arg.raw_value
                if "\\x" in val:
                    def hex_repl(match):
                        try:
                            return chr(int(match.group(1), 16))
                        except ValueError:
                            return match.group(0)
                    val = re.sub(r'\\x([0-9a-fA-F]{2})', hex_repl, val)
                    
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
                
            exe = cmd.executable
            if "\\x" in exe:
                exe = re.sub(r'\\x([0-9a-fA-F]{2})', lambda m: chr(int(m.group(1), 16)), exe)
            if "\\" in exe and re.search(r'\\[0-7]{3}', exe):
                exe = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m.group(1), 8)), exe)
                
            new_commands.append(SingleCommand(
                executable=exe,
                arguments=new_args,
                redirections=cmd.redirections,
                pipelines=cmd.pipelines,
                command_substitutions=cmd.command_substitutions,
                environment_references=cmd.environment_references,
                aliases=cmd.aliases,
                source_location=cmd.source_location
            ))
        return ParsedCommand(commands=new_commands)

class AliasResolutionPass(NormalizationPass):
    def __init__(self, aliases: Dict[str, str]):
        self.aliases = aliases
        
    def apply(self, ast: ParsedCommand) -> ParsedCommand:
        new_commands = []
        for cmd in ast.commands:
            exe = cmd.executable
            if exe in self.aliases:
                alias_cmd = self.aliases[exe]
                parts = alias_cmd.split(" ")
                new_exe = parts[0]
                new_args = []
                
                for p in parts[1:]:
                    new_args.append(CommandArgument(raw_value=p, resolved_value=p))
                    
                new_args.extend(cmd.arguments)
                
                new_commands.append(SingleCommand(
                    executable=new_exe,
                    arguments=new_args,
                    redirections=cmd.redirections,
                    pipelines=cmd.pipelines,
                    command_substitutions=cmd.command_substitutions,
                    environment_references=cmd.environment_references,
                    aliases=cmd.aliases + [exe],
                    source_location=cmd.source_location
                ))
            else:
                new_commands.append(cmd)
        return ParsedCommand(commands=new_commands)

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
        
        texts = []
        for cmd in current_ast.commands:
            texts.append(f"{cmd.executable} " + " ".join([a.resolved_value or a.raw_value for a in cmd.arguments]))
        normalized_text = " ; ".join(texts)
        
        return NormalizedCommand(
            original_hash="mockhash",
            normalized_text=normalized_text,
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
