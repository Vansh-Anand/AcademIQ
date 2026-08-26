from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict, Tuple
from .grammar import Grammar, Terminal, NonTerminal, Symbol, ProductionRule

@dataclass(frozen=True)
class AutomatonState:
    name: str

@dataclass(frozen=True)
class StackSymbol:
    value: Symbol

@dataclass(frozen=True)
class Transition:
    source_state: AutomatonState
    input_symbol: Optional[str]  # None for epsilon transition
    pop_symbol: Optional[StackSymbol]
    target_state: AutomatonState
    push_symbols: List[StackSymbol]

@dataclass(frozen=True)
class AutomatonConfiguration:
    state: AutomatonState
    stack: Tuple[StackSymbol, ...]

class PushdownAutomaton:
    """
    A Pushdown Automaton that tracks valid prefixes.
    For this phase, we use a simplified LL(1) / recursive descent style prefix matcher 
    acting over the CFG representation to validate token strings.
    """
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.initial_config = AutomatonConfiguration(
            state=AutomatonState("q0"),
            stack=(StackSymbol(grammar.start_symbol),)
        )
        
    def is_accepting(self, config: AutomatonConfiguration) -> bool:
        """Accepts if the stack is empty (all non-terminals resolved)."""
        return len(config.stack) == 0

    def is_valid_prefix(self, token_text: str, config: AutomatonConfiguration) -> bool:
        """
        Determines if the token_text is a valid prefix starting from the current config.
        We do a bounded DFS through epsilon expansions and terminal matches.
        """
        # If token is empty string, it's technically a valid prefix (no-op)
        if not token_text:
            return True
            
        return self._dfs_prefix_match(token_text, config.stack, 0)
        
    def _dfs_prefix_match(self, text: str, stack: Tuple[StackSymbol, ...], text_idx: int) -> bool:
        """
        Recursively expand the stack to see if it can match `text[text_idx:]`.
        This is a simplistic top-down parser for prefix matching.
        """
        if text_idx == len(text):
            return True # Successfully matched the whole prefix

        if not stack:
            return False # Stack empty but still have text to match -> Invalid

        top = stack[0].value
        rest_stack = stack[1:]

        if isinstance(top, Terminal):
            t_val = top.value
            remaining_text = text[text_idx:]
            
            # Check if Terminal starts with remaining text (prefix match on terminal)
            if t_val.startswith(remaining_text):
                return True
                
            # Check if remaining text starts with Terminal
            if remaining_text.startswith(t_val):
                return self._dfs_prefix_match(text, rest_stack, text_idx + len(t_val))
                
            return False
            
        elif isinstance(top, NonTerminal):
            # Expand NonTerminal
            rules = self.grammar.get_rules_for(top)
            for rule in rules:
                new_stack_symbols = tuple(StackSymbol(s) for s in rule.rhs)
                new_stack = new_stack_symbols + rest_stack
                
                if self._dfs_prefix_match(text, new_stack, text_idx):
                    return True
            return False
            
        return False
        
    def advance(self, text: str, config: AutomatonConfiguration) -> AutomatonConfiguration:
        """
        Advances the configuration by consuming the full `text`.
        Returns the new configuration. 
        Note: The actual LLM decoding step would advance character by character or token by token.
        """
        # Simplified advance: just re-calculate the stack after consuming text.
        # For full implementation, this uses the exact path found in prefix matching.
        # This is a stub for testing.
        return config # Placeholder
