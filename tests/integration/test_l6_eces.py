import pytest
import os
import json
import time

from l6_eces.crypto.hasher import HashProvider, CanonicalSerializer
from l6_eces.crypto.signer import SoftwareSigner
from l6_eces.chain.store import EvidenceStore
from l6_eces.chain.writer import EvidenceChainWriter
from l6_eces.forensics.verifier import EvidenceVerifier
from common.events.schemas import ToolInvocationEvent

@pytest.fixture
def temp_store(tmp_path):
    store_dir = str(tmp_path / "evidence")
    store = EvidenceStore(directory=store_dir)
    return store

@pytest.fixture
def crypto_components():
    hasher = HashProvider()
    signer = SoftwareSigner()
    signer.generate_key()
    return hasher, signer

def test_chain_creation_and_verification(temp_store, crypto_components):
    hasher, signer = crypto_components
    writer = EvidenceChainWriter(temp_store, hasher, signer)
    
    # Add a few events
    for i in range(3):
        evt = ToolInvocationEvent(
            event_id=f"test-{i}",
            tool_name="cat",
            arguments={"path": "/tmp/test"},
            timestamp_ns=time.time_ns(),
            layer="L1",
            trace_id="test-trace"
        )
        writer.append_event(evt, source_layer="L1")
        
    records = temp_store.read_all()
    assert len(records) == 4 # Genesis + 3 events
    
    verifier = EvidenceVerifier(signer)
    result = verifier.verify_chain(records)
    
    assert result.valid is True
    assert result.records_checked == 4
    assert result.signature_status == "PASS"

def test_tampering_payload_modification(temp_store, crypto_components):
    hasher, signer = crypto_components
    writer = EvidenceChainWriter(temp_store, hasher, signer)
    
    evt = ToolInvocationEvent(
        event_id="test-t1",
        tool_name="cat",
        arguments={"path": "/tmp/safe"},
        timestamp_ns=time.time_ns(),
        layer="L1",
        trace_id="test-trace"
    )
    writer.append_event(evt, source_layer="L1")
    
    # Tamper the file directly
    records = temp_store.read_all()
    assert len(records) == 2
    
    # Modify the payload in the file
    lines = []
    with open(temp_store.chain_file, "r") as f:
        lines = f.readlines()
        
    tampered_lines = []
    for line in lines:
        if line.startswith("E|"):
            type_flag, json_data = line.split("|", 1)
            data = json.loads(json_data)
            data["payload"]["arguments"]["path"] = "/etc/shadow" # TAMPER
            tampered_lines.append(f"E|{json.dumps(data)}\n")
        else:
            tampered_lines.append(line)
            
    with open(temp_store.chain_file, "w") as f:
        f.writelines(tampered_lines)
        
    tampered_records = temp_store.read_all()
    verifier = EvidenceVerifier(signer)
    result = verifier.verify_chain(tampered_records)
    
    assert result.valid is False
    assert result.failure_type == "PAYLOAD_HASH_MISMATCH"
    assert result.first_failure_sequence == 1

def test_tampering_chain_break(temp_store, crypto_components):
    hasher, signer = crypto_components
    writer = EvidenceChainWriter(temp_store, hasher, signer)
    
    for i in range(2):
        evt = ToolInvocationEvent(
            event_id=f"test-b{i}",
            tool_name="ls",
            arguments={},
            timestamp_ns=time.time_ns(),
            layer="L1",
            trace_id="test-trace"
        )
        writer.append_event(evt, source_layer="L1")
        
    # Delete the middle record to simulate missing log
    lines = []
    with open(temp_store.chain_file, "r") as f:
        lines = f.readlines()
        
    # Remove sequence 1
    tampered_lines = [lines[0], lines[2]] # Genesis, Seq 2
    
    with open(temp_store.chain_file, "w") as f:
        f.writelines(tampered_lines)
        
    tampered_records = temp_store.read_all()
    verifier = EvidenceVerifier(signer)
    result = verifier.verify_chain(tampered_records)
    
    assert result.valid is False
    assert result.failure_type == "SEQUENCE_MISMATCH"

def test_redaction_policy():
    from l6_eces.redaction.policy import EvidenceRedactionPolicy
    
    policy = EvidenceRedactionPolicy(mode="STANDARD")
    raw = {
        "user": "admin",
        "password": "supersecretpassword",
        "config": {
            "api_key": "sk-12345",
            "command": "Bearer xyz123"
        }
    }
    
    redacted = policy.redact(raw)
    
    assert redacted["user"] == "admin"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["config"]["api_key"] == "[REDACTED]"
    assert redacted["config"]["command"] == "[REDACTED_TOKEN]"
