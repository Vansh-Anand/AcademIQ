import yaml
from .grammar import Grammar, StartSymbol, NonTerminal, Terminal, ProductionRule
from .interfaces import GCDPolicyCompiler
from typing import List

class YamlGCDCompiler(GCDPolicyCompiler):
    def compile_policy(self, policy_config: dict) -> Grammar:
        """
        Compiles the dictionary configuration (from gcd.yaml) into a CFG.
        Creates a language that permits tool calls based on the policy.
        Example syntax we want to allow:
        tool_name("safe_argument")
        """
        start = StartSymbol("S")
        tool_call = NonTerminal("TOOL_CALL")
        
        rules: List[ProductionRule] = []
        
        # S -> TOOL_CALL
        rules.append(ProductionRule(start, [tool_call]))
        
        allowed_tools = policy_config.get("allowed_tools", [])
        
        for tool in allowed_tools:
            tool_nt = NonTerminal(f"TOOL_{tool.upper()}")
            # TOOL_CALL -> TOOL_XXX
            rules.append(ProductionRule(tool_call, [tool_nt]))
            
            # TOOL_XXX -> tool_name ( ARG )
            rules.append(ProductionRule(
                tool_nt, 
                [Terminal(tool), Terminal("("), NonTerminal(f"ARG_{tool.upper()}"), Terminal(")")]
            ))
            
            # Simple argument policy for demonstration:
            # We will allow specific arguments based on tool type
            arg_nt = NonTerminal(f"ARG_{tool.upper()}")
            
            if tool == "shell":
                allowed_cmds = policy_config.get("allowed_shell_commands", [])
                for cmd in allowed_cmds:
                    # Allow quotes around command
                    rules.append(ProductionRule(arg_nt, [Terminal('"'), Terminal(cmd), Terminal('"')]))
            elif tool == "read_file":
                # Let's say read_file allows a specific safe path
                rules.append(ProductionRule(arg_nt, [Terminal('"'), Terminal("/app/config.yaml"), Terminal('"')]))
                rules.append(ProductionRule(arg_nt, [Terminal('"'), Terminal("/safe/file.txt"), Terminal('"')]))
            else:
                rules.append(ProductionRule(arg_nt, [Terminal('""')]))

        return Grammar(start_symbol=start, rules=rules)
