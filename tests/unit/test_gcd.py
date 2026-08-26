import pytest
import numpy as np
from l1_gcd.tokenizer import MockTokenizer
from l1_gcd.grammar import Grammar, StartSymbol, Terminal, NonTerminal, ProductionRule
from l1_gcd.automaton import PushdownAutomaton
from l1_gcd.adapters import DeterministicDecoderAdapter

@pytest.fixture
def basic_grammar():
    start = StartSymbol("S")
    tool_call = NonTerminal("TOOL_CALL")
    arg_nt = NonTerminal("ARG_READ_FILE")
    
    rules = [
        ProductionRule(start, [tool_call]),
        ProductionRule(tool_call, [Terminal("read_file"), Terminal("("), arg_nt, Terminal(")")]),
        ProductionRule(arg_nt, [Terminal('"'), Terminal("/safe/file.txt"), Terminal('"')])
    ]
    return Grammar(start, rules)

@pytest.fixture
def mock_tokenizer():
    vocab = {
        0: "read_file",
        1: "delete_file",
        2: "(",
        3: ")",
        4: '"',
        5: "/safe/file.txt",
        6: "/etc/passwd"
    }
    return MockTokenizer(vocab)

def test_forbidden_tool_cannot_be_sampled(basic_grammar, mock_tokenizer):
    pda = PushdownAutomaton(basic_grammar)
    adapter = DeterministicDecoderAdapter(mock_tokenizer)
    
    # We set up mock logits where the forbidden token "delete_file" (id=1) has the HIGHEST probability
    vocab_size = mock_tokenizer.vocab_size()
    mock_logits = np.zeros(vocab_size)
    
    mock_logits[0] = 5.0  # read_file (legal)
    mock_logits[1] = 100.0 # delete_file (illegal, highly probable in raw)
    
    selected_id, raw_probs, masked_probs = adapter.decode_with_constraints(
        prompt="system: generate tool", 
        automaton=pda, 
        mock_logits=mock_logits
    )
    
    # Assert raw probability of illegal token was high
    assert raw_probs[1] > 0.99
    
    # Assert masked probability of illegal token is EXACTLY 0.0
    assert masked_probs[1] == 0.0
    
    # Assert the selected token is the legal one, despite raw logits
    assert selected_id == 0

def test_legal_high_probability_token_is_preserved(basic_grammar, mock_tokenizer):
    pda = PushdownAutomaton(basic_grammar)
    adapter = DeterministicDecoderAdapter(mock_tokenizer)
    
    vocab_size = mock_tokenizer.vocab_size()
    mock_logits = np.zeros(vocab_size)
    
    # Two legal prefix options technically (though grammar only allows read_file, 
    # let's assume 'read_file' (0) and '"' (4) are in vocab, but from start state only 0 is legal)
    mock_logits[0] = 10.0 # read_file
    mock_logits[1] = 50.0 # delete_file (illegal)
    
    selected_id, raw_probs, masked_probs = adapter.decode_with_constraints(
        prompt="sys", 
        automaton=pda, 
        mock_logits=mock_logits
    )
    
    assert masked_probs[0] > 0.99 # It becomes ~1.0 because the competitor is masked to -inf
    assert masked_probs[1] == 0.0
