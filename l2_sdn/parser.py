import bashlex
from typing import List, Dict, Any, Optional
from .events import ParsedCommand, CommandArgument

class BashlexCommandParser:
    """
    Parses a shell command into a structured AST using bashlex.
    Extracts the executable, arguments, and handles substitutions/redirections safely
    without executing anything.
    """
    
    def parse(self, command_text: str) -> ParsedCommand:
        try:
            nodes = bashlex.parse(command_text)
        except Exception as e:
            raise ValueError(f"Failed to parse shell command: {e}")
            
        if not nodes:
            return ParsedCommand(executable="", arguments=[])
            
        # We handle the first command node for simplicity, 
        # though a real implementation would iterate and build a complex AST tree.
        node = nodes[0]
        
        executable = ""
        arguments = []
        redirections = []
        pipelines = False
        command_substitutions = []
        environment_references = []
        
        class ASTVisitor(bashlex.ast.nodevisitor):
            def __init__(self):
                self.parts = []
                self.redirects = []
                self.command_subs = []
                self.env_refs = []
                
            def visitcommand(self, n, parts):
                pass
                
            def visitword(self, n, parts):
                self.parts.append(n.word)
                
            def visitcommandsubstitution(self, n, parts):
                self.command_subs.append(command_text[n.pos[0]:n.pos[1]])
                # Mark that this word contains a command substitution
                if self.parts:
                    self.parts[-1] += " $(...)"
                else:
                    self.parts.append("$(...)")
                    
            def visitparameter(self, n, parts):
                self.env_refs.append(n.value)
                
            def visitredirect(self, n, parts):
                self.redirects.append(command_text[n.pos[0]:n.pos[1]])
                
            def visitpipeline(self, n, parts):
                nonlocal pipelines
                pipelines = True
                
        visitor = ASTVisitor()
        visitor.visit(node)
        
        if visitor.parts:
            executable = visitor.parts[0]
            for arg_text in visitor.parts[1:]:
                arguments.append(CommandArgument(
                    raw_value=arg_text,
                    is_substitution="$(" in arg_text or "`" in arg_text,
                    is_variable="$" in arg_text
                ))
                
        return ParsedCommand(
            executable=executable,
            arguments=arguments,
            redirections=visitor.redirects,
            pipelines=pipelines,
            command_substitutions=visitor.command_subs,
            environment_references=visitor.env_refs
        )
