from dataclasses import dataclass
from typing import List, Union, Set

@dataclass(frozen=True)
class Terminal:
    value: str

@dataclass(frozen=True)
class NonTerminal:
    name: str

@dataclass(frozen=True)
class StartSymbol(NonTerminal):
    pass

Symbol = Union[Terminal, NonTerminal]

@dataclass(frozen=True)
class ProductionRule:
    lhs: NonTerminal
    rhs: List[Symbol]

class Grammar:
    def __init__(self, start_symbol: StartSymbol, rules: List[ProductionRule]):
        self.start_symbol = start_symbol
        self.rules = rules
        
        self.non_terminals: Set[NonTerminal] = {start_symbol}
        self.terminals: Set[Terminal] = set()
        
        for rule in rules:
            self.non_terminals.add(rule.lhs)
            for symbol in rule.rhs:
                if isinstance(symbol, NonTerminal):
                    self.non_terminals.add(symbol)
                elif isinstance(symbol, Terminal):
                    self.terminals.add(symbol)
                    
    def get_rules_for(self, non_terminal: NonTerminal) -> List[ProductionRule]:
        return [rule for rule in self.rules if rule.lhs == non_terminal]
