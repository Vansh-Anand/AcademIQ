import pytest
import os
from l2_sdn.parser import BashlexCommandParser
from l2_sdn.normalizers import get_default_normalizer
from l2_sdn.canonicalizer import CommandCanonicalizer

def test_parser_basic():
    parser = BashlexCommandParser()
    ast = parser.parse("cat /etc/passwd")
    
    assert ast.executable == "cat"
    assert len(ast.arguments) == 1
    assert ast.arguments[0].raw_value == "/etc/passwd"
    assert ast.pipelines is False
    
def test_parser_quotes():
    parser = BashlexCommandParser()
    # Shlex correctly handles quotes and strips them during parsing
    ast = parser.parse('read_file "/etc/passwd" "other file.txt"')
    
    assert ast.executable == "read_file"
    assert ast.arguments[0].raw_value == "/etc/passwd"
    assert ast.arguments[1].raw_value == "other file.txt"

def test_canonicalizer():
    # Setup dummy normalizer
    norm = get_default_normalizer()
    parser = BashlexCommandParser()
    ast = parser.parse("cat /tmp/../etc/passwd")
    norm_ast = norm.normalize(ast)
    
    canonicalizer = CommandCanonicalizer()
    canon_ast = canonicalizer.canonicalize(norm_ast)
    
    # Check if the path traversal was correctly resolved
    paths = [p.canonical_path for p in canon_ast.canonical_paths if p.canonical_path]
    # On Windows it will prepend drive, but we know it should resolve to /etc/passwd effectively
    assert any("etc" in p and "passwd" in p and "tmp" not in p for p in paths)
