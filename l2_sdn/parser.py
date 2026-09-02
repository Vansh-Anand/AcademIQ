import bashlex
from typing import List, Dict, Any, Optional
from .events import ParsedCommand, SingleCommand, CommandArgument

class BashlexCommandParser:
    """
    Parses a shell command into a structured AST using bashlex.
    Extracts the executables, arguments, and handles substitutions/redirections safely
    across pipelines and logical operators without executing anything.
    """
    
    def parse(self, command_text: str) -> ParsedCommand:
        try:
            nodes = bashlex.parse(command_text)
        except Exception as e:
            raise ValueError(f"Failed to parse shell command: {e}")
            
        if not nodes:
            return ParsedCommand(commands=[])
            
        single_commands = []
        
        class CommandVisitor(bashlex.ast.nodevisitor):
            def __init__(self):
                self.commands = []
                
            def visitcommand(self, n, parts):
                words = []
                redirects = []
                command_subs = []
                env_refs = []
                
                class WordVisitor(bashlex.ast.nodevisitor):
                    def visitword(self, w, wp):
                        words.append(w.word)
                    def visitcommandsubstitution(self, c, cp):
                        command_subs.append(command_text[c.pos[0]:c.pos[1]])
                        if words:
                            words[-1] += " $(...)"
                        else:
                            words.append("$(...)")
                    def visitparameter(self, p, pp):
                        env_refs.append(p.value)
                    def visitredirect(self, r, *args):
                        redirects.append(command_text[r.pos[0]:r.pos[1]])
                        
                wv = WordVisitor()
                wv.visit(n)
                
                if words:
                    executable = words[0]
                    arguments = []
                    for arg_text in words[1:]:
                        arguments.append(CommandArgument(
                            raw_value=arg_text,
                            is_substitution="$(" in arg_text or "`" in arg_text,
                            is_variable="$" in arg_text
                        ))
                    self.commands.append(SingleCommand(
                        executable=executable,
                        arguments=arguments,
                        redirections=redirects,
                        pipelines=True,
                        command_substitutions=command_subs,
                        environment_references=env_refs
                    ))
                    
        visitor = CommandVisitor()
        for node in nodes:
            visitor.visit(node)
            
        return ParsedCommand(commands=visitor.commands)

