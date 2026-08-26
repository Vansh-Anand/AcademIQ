import yaml
import json
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class AcademiqConfig:
    agent: Dict[str, Any]
    gcd: Dict[str, Any]
    sdn: Dict[str, Any]
    toctou: Dict[str, Any]
    ebpf: Dict[str, Any]
    divergence: Dict[str, Any]
    ece: Dict[str, Any]
    hpc: Dict[str, Any]
    riskchain: Dict[str, Any]
    governance: Dict[str, Any]
    enforcement: Dict[str, Any]
    eces: Dict[str, Any]
    tee: Dict[str, Any]
    forensics: Dict[str, Any]
    development: Dict[str, Any]

def load_config(path: str) -> AcademiqConfig:
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Note: Full pydantic/jsonschema validation would normally happen here.
    # For Phase 1 scaffold, we load into the dataclass directly.
    return AcademiqConfig(**data)
