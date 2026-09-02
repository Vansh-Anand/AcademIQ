import pytest
import os
from l2_sdn.parser import BashlexCommandParser
from l2_sdn.normalizers import get_default_normalizer
from l2_sdn.canonicalizer import CommandCanonicalizer

def test_parser_basic():
    parser = BashlexCommandParser()
    ast = parser.parse("cat /etc/passwd")
    
    assert len(ast.commands) == 1
    assert ast.commands[0].executable == "cat"
    assert len(ast.commands[0].arguments) == 1
    assert ast.commands[0].arguments[0].raw_value == "/etc/passwd"
    
def test_parser_quotes():
    parser = BashlexCommandParser()
    ast = parser.parse('read_file "/etc/passwd" "other file.txt"')
    
    assert len(ast.commands) == 1
    assert ast.commands[0].executable == "read_file"
    assert ast.commands[0].arguments[0].raw_value == "/etc/passwd"
    assert ast.commands[0].arguments[1].raw_value == "other file.txt"

def test_parser_compound_commands():
    parser = BashlexCommandParser()
    
    # 1. Logical AND
    ast = parser.parse("ls -la && rm -rf /")
    assert len(ast.commands) == 2
    assert ast.commands[0].executable == "ls"
    assert ast.commands[1].executable == "rm"
    
    # 2. Pipeline
    ast = parser.parse("echo 'cat /etc/passwd' | bash")
    assert len(ast.commands) == 2
    assert ast.commands[0].executable == "echo"
    assert ast.commands[1].executable == "bash"
    
    # 3. Mixed
    ast = parser.parse("ls | grep x && rm -rf /")
    assert len(ast.commands) == 3
    assert ast.commands[0].executable == "ls"
    assert ast.commands[1].executable == "grep"
    assert ast.commands[2].executable == "rm"
    
    # 4. Semicolon
    ast = parser.parse("echo hello ; rm -rf /")
    assert len(ast.commands) == 2
    assert ast.commands[0].executable == "echo"
    assert ast.commands[1].executable == "rm"

def test_canonicalizer():
    norm = get_default_normalizer()
    parser = BashlexCommandParser()
    ast = parser.parse("cat /tmp/../etc/passwd")
    norm_ast = norm.normalize(ast)
    
    canonicalizer = CommandCanonicalizer()
    canon_ast = canonicalizer.canonicalize(norm_ast)
    
    assert len(canon_ast.commands) == 1
    paths = [p.canonical_path for p in canon_ast.commands[0].canonical_paths if p.canonical_path]
    assert any("etc" in p and "passwd" in p and "tmp" not in p for p in paths)

