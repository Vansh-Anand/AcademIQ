from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import time
import hashlib

class CommandPath(BaseModel):
    raw_path: str
    canonical_path: Optional[str] = None
    path_type: str = "UNKNOWN" # FILE, DIRECTORY, SYMLINK, UNKNOWN
    source_argument_index: int = -1
    source_ast_location: Optional[str] = None

class CommandArgument(BaseModel):
    raw_value: str
    resolved_value: Optional[str] = None
    is_path: bool = False
    is_substitution: bool = False
    is_variable: bool = False

class RawShellCommand(BaseModel):
    command_text: str
    shell_type: str = "sh"
    timestamp_ns: int = Field(default_factory=time.time_ns)
    session_id: str
    trace_id: str

class SingleCommand(BaseModel):
    executable: str
    arguments: List[CommandArgument]
    redirections: List[str] = []
    pipelines: bool = False
    command_substitutions: List[str] = []
    environment_references: List[str] = []
    aliases: List[str] = []
    source_location: str = "stdin"

class ParsedCommand(BaseModel):
    commands: List[SingleCommand]

class NormalizedCommand(BaseModel):
    original_hash: str
    normalized_text: str
    normalized_ast: ParsedCommand
    transformations_applied: List[Dict[str, Any]] = []

class SingleCanonicalCommand(BaseModel):
    executable: str
    canonical_arguments: List[str]
    canonical_paths: List[CommandPath]
    canonical_environment: Dict[str, str] = {}
    canonical_redirections: List[str] = []
    canonical_text: str

class CanonicalCommand(BaseModel):
    commands: List[SingleCanonicalCommand]
    canonical_text: str
    command_hash: str

class NormalizationTrace(BaseModel):
    original_hash: str
    passes: List[Dict[str, Any]] = []
    before_hash: str
    after_hash: str
    transformations: List[Dict[str, Any]] = []
    policy_version: str = "1.0"
    normalizer_version: str = "1.0"

class NormalizedCommandEvent(BaseModel):
    event_id: str
    schema_version: str = "1.0"
    session_id: str
    trace_id: str
    agent_id: str = "unknown"
    timestamp_ns: int = Field(default_factory=time.time_ns)
    command_text: str = ""
    original_command_hash: str
    canonical_command_hash: str
    normalization_passes: List[str] = []
    obfuscation_detected: bool = False
    transformations: List[Dict[str, Any]] = []
    policy_result: str = "UNKNOWN"
    matched_rule: Optional[str] = None
    path_identities: List[Dict[str, Any]] = []
    toctou_result: Optional[str] = None
    security_decision: str = "BLOCK"
