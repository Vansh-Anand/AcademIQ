import pytest
import os
from l2_sdn.parser import ShlexCommandParser
from l2_sdn.normalizers import PathNormalizer

def test_parser_basic():
    parser = ShlexCommandParser()
    ast = parser.parse("cat /etc/passwd")
    
    assert ast["executable"] == "cat"
    assert ast["arguments"] == ["/etc/passwd"]
    assert ast["flags"]["has_pipeline"] is False
    
def test_parser_quotes():
    parser = ShlexCommandParser()
    # Shlex correctly handles quotes and strips them during parsing
    ast = parser.parse('read_file "/etc/passwd" "other file.txt"')
    
    assert ast["executable"] == "read_file"
    assert ast["arguments"] == ["/etc/passwd", "other file.txt"]

def test_path_normalizer():
    normalizer = PathNormalizer()
    ast = {
        "executable": "cat",
        "arguments": ["/etc/../etc/passwd", "./local_file.txt", "non_path_arg"]
    }
    
    norm_ast = normalizer.apply(ast)
    
    # PathNormalizer should syntactically resolve .. and .
    assert norm_ast["arguments"][0] == "/etc/passwd"
    assert norm_ast["arguments"][1] == "local_file.txt"
    assert norm_ast["arguments"][2] == "non_path_arg"
